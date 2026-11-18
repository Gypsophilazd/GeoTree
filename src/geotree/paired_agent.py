"""Shared E02-F2 Harbor entry point. Only the feedback toggle differs."""
import asyncio,json,os,re,time
from pathlib import Path
from geotree.paths import runtime_dir
from harbor.agents.base import BaseAgent
from harbor.agents.capabilities import AgentCapabilities
from geotree.geometry_reader import FixedGeometryReader
from geotree.geometry_feedback import GeometryFeedbackExecutor
from geotree.nosearch import ObservationBuilder,ActionValidator,NoSearch,FeedbackRecorder

class Budget:
    def __init__(self,end):self.end=end;self.cad=0;self.tokens=0
    def remaining(self):return self.end-time.time()
    async def bound(self,call,seconds):
        remaining=min(seconds,self.remaining())
        if remaining<=0:raise TimeoutError('trial_deadline')
        return await asyncio.wait_for(call(),remaining)
    def usage(self,u):
        if not isinstance(u,dict) or any(type(u.get(k)) is not int or u[k]<0 for k in ('input_tokens','output_tokens')):
            raise RuntimeError('missing or invalid token telemetry')
        self.tokens+=u['input_tokens']+u['output_tokens']

def atomic(path,obj):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj));tmp.replace(path)

class Mailbox:
    def __init__(self,root,budget):self.root=root;self.budget=budget
    async def propose(self,obs):
        i=obs['turn'];end=min(self.budget.end,time.time()+420)
        atomic(self.root/f'observation-{i}.json',dict(observation=obs,deadline=end))
        p=self.root/f'action-{i}.json'
        while time.time()<end:
            if (self.root/'relay-error.json').exists():raise RuntimeError('relay_error')
            if p.exists():
                if p.stat().st_size>65536:raise ValueError('oversize reply')
                r=json.loads(p.read_text(encoding='utf-8-sig'))
                if time.time()>=end:break
                return r['action'],r['usage']
            await asyncio.sleep(.15)
        raise TimeoutError('trial_deadline' if self.budget.remaining()<=0 else 'model_deadline')

class Executor:
    def __init__(self,env,logs,budget):
        self.env=env;self.logs=logs;self.budget=budget
    async def execute(self,p):
        if p.action=='check_workspace':
            command="test -d /app && test -f /app/6b54209a13.png && printf 'workspace_and_drawing_ok\\n'"
            limit=10
        else:
            if self.budget.cad>=2:return {'status':'rejected','error':'cad_budget_exhausted'}
            async def prepare():
                guard=await self.env.exec('test ! -L /app/answer.py && test ! -L /app/answer.FCStd && rm -f -- /app/answer.FCStd',cwd='/app',user='65534',timeout_sec=10)
                if guard.return_code:raise RuntimeError('output preparation failed')
                f=self.logs/f'{p.request_id}.py';f.write_text(p.code)
                await self.env.upload_file(f,'/app/answer.py')
            await self.budget.bound(prepare,15)
            limit=min(60,self.budget.remaining())
            if limit<1:raise TimeoutError('trial_deadline')
            self.budget.cad+=1
            # Container-side deadline, not just a timeout on the Docker client.
            command=f'exec timeout --signal=KILL {limit:.3f}s env HOME=/tmp/geotree-home OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /opt/conda/bin/python -I /app/answer.py'
        t=time.monotonic()
        r=await self.budget.bound(lambda:self.env.exec(command,cwd='/app',user='65534',timeout_sec=int(limit)+3),limit+3)
        return dict(status='executed',command=command,exit_status=r.return_code,stdout=(r.stdout or '')[:12000],stderr=(r.stderr or '')[:12000],elapsed_sec=time.monotonic()-t)

class Runtime:
    def __init__(self,provider,executor,recorder,budget):
        self.provider=provider;self.executor=executor;self.recorder=recorder;self.budget=budget
    async def run(self,instruction):
        history=[];status='decision_budget_exhausted';n=0
        try:
            for turn in range(4):
                if self.budget.remaining()<=0:status='trial_deadline';break
                if self.budget.tokens>=200000:status='token_soft_budget';break
                obs=ObservationBuilder().build(instruction,history,turn,4)
                self.recorder.record('observation',obs);n+=1
                payload=None
                try:
                    payload,usage=await self.budget.bound(lambda:self.provider.propose(obs),420)
                    self.recorder.record('model_reply',{'payload':payload,'usage':usage});self.budget.usage(usage)
                    p=NoSearch().select([ActionValidator().check(payload,obs)])
                except (ValueError,TypeError,KeyError,SyntaxError) as e:
                    feedback={'status':'rejected','error':str(e)}
                else:
                    if p.action=='done':
                        self.recorder.step(payload,{'status':'done'});status='done';break
                    if self.budget.tokens>=200000:
                        status='token_soft_budget';self.recorder.step(payload,{'status':status});break
                    if p.action=='run_freecad' and self.budget.cad>=2:
                        status='cad_budget_exhausted';self.recorder.step(payload,{'status':status});break
                    try:feedback=await self.executor.execute(p)
                    except TimeoutError:feedback={'status':'timeout'}
                    except Exception as e:feedback={'status':'execution_error','error':type(e).__name__}
                history.append(feedback);self.recorder.record('feedback',feedback);self.recorder.step(payload,feedback)
        except TimeoutError:
            status='trial_deadline' if self.budget.remaining()<=0 else 'model_deadline'
        except BaseException as e:
            status='runtime_error';self.recorder.record('fatal',{'type':type(e).__name__,'message':str(e)});raise
        finally:
            self.recorder.record('terminal',dict(status=status,decisions=n,cad_runs=self.budget.cad,tokens=self.budget.tokens,overshoot=max(0,self.budget.tokens-200000)))
        return status

class BoundObserver(FixedGeometryReader):
    async def __call__(self):
        try:return await super().__call__()
        except (Exception,asyncio.CancelledError) as e:
            with (self.logs_dir/'observer-failures.jsonl').open('a') as f:
                f.write(json.dumps({'action_id':self.action_id,'time':time.time(),'status':type(e).__name__})+'\n')
            raise

class PairedAgent(BaseAgent):
    capabilities=AgentCapabilities(atif=True)
    @staticmethod
    def name():return 'geotree-paired-dev'
    def version(self):return '0.2.0'
    async def setup(self,environment):
        trial=os.environ['GEOTREE_PAIR_TRIAL']
        if not re.fullmatch(r'f2-[0-9a-f]{16}-a[01]',trial) or self.model_name:raise ValueError('invalid pair configuration')
        self.root=(runtime_dir()/'f2')/trial/'mailbox'
        self.root.mkdir(mode=0o700,parents=False,exist_ok=False)
        self.budget=Budget(float(os.environ['GEOTREE_PAIR_DEADLINE']))
        r=await self.budget.bound(lambda:environment.exec('install -d -o 65534 -g 65534 -m 700 /tmp/geotree-home && chown 65534:65534 /app && chmod 700 /logs && command -v timeout',timeout_sec=10),12)
        if r.return_code:raise RuntimeError('setup failed')
        r=await self.budget.bound(lambda:environment.exec('test ! -r /logs && test ! -x /logs && test ! -r /logs/verifier && test ! -S /var/run/docker.sock',user='65534',timeout_sec=5),7)
        if r.return_code:raise RuntimeError('execution isolation check failed')
        self.reader=BoundObserver(environment,self.logs_dir)
        # Install in both groups to keep tool surface identical.
        await self.budget.bound(self.reader.setup,30)
        self.geometry=trial.endswith('-a1')
    async def run(self,instruction,environment,context):
        status='error'
        try:
            await self.budget.bound(lambda:environment.download_file('/app/6b54209a13.png',self.root/'drawing.png'),15)
            executor=Executor(environment,self.logs_dir,self.budget)
            if self.geometry:
                observer=GeometryFeedbackExecutor(executor,self.reader,timeout_sec=10)
                async def execute(p):
                    self.reader.action_id=p.request_id
                    result=await observer.execute(p)
                    if 'geometry_observer' in result:result['geometry_observer']['action_id']=p.request_id
                    return result
                from types import SimpleNamespace
                executor=SimpleNamespace(execute=execute)
            runtime=Runtime(Mailbox(self.root,self.budget),executor,FeedbackRecorder(self.logs_dir),self.budget)
            status=await self.budget.bound(lambda:runtime.run(instruction),1200)
        finally:atomic(self.root/'terminal.json',{'status':status})
