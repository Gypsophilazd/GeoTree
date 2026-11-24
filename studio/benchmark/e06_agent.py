"""Both recovery arms use the same bounded HTTP relay protocol and executor."""
import asyncio,json,time,hashlib,os
from pathlib import Path

from geotree.enhanced_agent_l import EnhancedAgent,ROOT,INSTRUCTION_SHA,TextExecutor,EnhancedFeedback
from geotree.nosearch import ActionValidator,FeedbackRecorder,NoSearch,ObservationBuilder
from geotree.paired_agent import atomic,Mailbox,Budget

MODEL_SEC=600
WALL_SEC=2600

class RecoveryMailbox(Mailbox):
    async def propose(self, obs):
        i=obs['turn']
        end=min(self.budget.end,time.time()+MODEL_SEC)
        atomic(self.root/f'observation-{i}.json',dict(observation=obs,deadline=end))
        path=self.root/f'action-{i}.json'
        while time.time()<end:
            if (self.root/'relay-error.json').exists():raise RuntimeError('relay_error')
            if path.exists():
                if path.stat().st_size>65536:raise ValueError('oversize reply')
                packet=json.loads(path.read_bytes())
                return packet['action'],packet['usage']
            await asyncio.sleep(.15)
        raise TimeoutError('trial_deadline' if self.budget.remaining()<=0 else 'model_deadline')

class RecoveryRuntime:
    def __init__(self,provider,executor,recorder,budget):
        self.provider,self.executor,self.recorder,self.budget=provider,executor,recorder,budget

    async def run(self,instruction):
        history=[]; status='decision_budget_exhausted'; n=0; last_code=''
        try:
            for turn in range(4):
                if self.budget.remaining()<=0:status='trial_deadline';break
                if self.budget.tokens>=200000:status='token_soft_budget';break
                obs=ObservationBuilder().build(instruction,history,turn,4)
                obs['allowed_actions']=['run_freecad','done']
                obs['workspace']='PASS: container workspace writable and setup complete'
                obs['cad_remaining']=2-self.budget.cad
                if last_code:obs['last_cad_script']=last_code
                # Explicitly say that loops/conditionals are compatible with the existing AST validator.
                obs['script_policy']=obs['script_policy'].replace('Straight-line Python only:', 'Bounded Python (loops and conditionals allowed):')
                if os.environ.get('E06_VALIDATOR_HINT')=='1':
                    obs['script_policy'] += ' Do not put slash characters into any string except the exact save path; inside FreeCAD expression strings use times 0.5 instead of division by 2, and avoid using paths in comments passed as strings; never use setattr or getattr. Arithmetic division in Python numeric expressions is allowed.'

                self.recorder.record('observation',obs);n+=1;payload=None
                try:
                    payload,usage=await self.provider.propose(obs)
                    self.recorder.record('model_reply',{'payload':payload,'usage':usage})
                    self.budget.usage(usage)
                    p=NoSearch().select([ActionValidator().check(payload,obs)])
                    if p.action not in obs['allowed_actions']:raise ValueError('action not allowed; workspace already checked')
                    if p.action=='done' and not any(x.get('artifact_exists') for x in history):
                        raise ValueError('no successful CAD artifact; use run_freecad')
                except (ValueError,TypeError,KeyError,SyntaxError) as e:
                    feedback={'status':'rejected','error':str(e)}
                else:
                    if p.action=='done':
                        self.recorder.step(payload,{'status':'done'});status='done';break
                    if self.budget.tokens>=200000:
                        status='token_soft_budget';self.recorder.step(payload,{'status':status});break
                    if self.budget.cad>=2:
                        status='cad_budget_exhausted';self.recorder.step(payload,{'status':status});break
                    last_code=p.code
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

class ArtifactFeedback:
    def __init__(self,base,env,budget):self.base,self.env,self.budget=base,env,budget
    async def execute(self,p):
        raw=await self.base.execute(p)
        if p.action=='run_freecad':
            if raw.get('exit_status')==0:
                cmd='test ! -L /app/answer.FCStd && test -s /app/answer.FCStd && test -s /app/answer.py'
                r=await self.budget.bound(lambda:self.env.exec(cmd,cwd='/app',user='65534',timeout_sec=5),5)
                raw['artifact_exists']=r.return_code==0
            else:raw['artifact_exists']=False
        return raw

class RecoveryAgent(EnhancedAgent):
    @staticmethod
    def name():return 'geotree-enhanced-l-recovery'
    async def run(self, instruction, environment, context) -> None:
        status='error'
        try:
            frozen=Path(os.environ['E06_PUBLIC']).read_bytes()
            if hashlib.sha256(frozen).hexdigest()!=os.environ['E06_PUBLIC_SHA'] or instruction.strip()!=frozen.decode().strip():
                raise ValueError('task_instruction_mismatch')
            text=frozen.decode().strip()
            p=self.logs_dir/'public-instruction.md';p.write_text(text,encoding='utf-8')
            await self.budget.bound(lambda:environment.upload_file(p,'/opt/geotree-k/instruction.md'),8)
            r=await self.budget.bound(lambda:environment.exec('chown root:root /opt/geotree-k/instruction.md && chmod 444 /opt/geotree-k/instruction.md',timeout_sec=5),7)
            if r.return_code:raise RuntimeError('public_instruction_install')
            base=TextExecutor(environment,self.logs_dir,self.budget)
            workspace=await base.execute(type('WorkspaceCheck',(),{'action':'check_workspace'})())
            atomic(self.logs_dir/'workspace-init.json',workspace)
            if workspace.get('exit_status')!=0:raise RuntimeError('workspace_init')
            ex=ArtifactFeedback(base,environment,self.budget)
            if self.enabled:ex=EnhancedFeedback(ex,environment,self.logs_dir,self.budget,hashlib.sha256(text.encode()).hexdigest())
            runtime=RecoveryRuntime(RecoveryMailbox(self.root,self.budget),ex,FeedbackRecorder(self.logs_dir),self.budget)
            status=await runtime.run(text)
        finally:
            if context is not None:
                context.metadata={**(context.metadata or {}),'geotree_terminal':status,'geotree_cad_runs':self.budget.cad}
            checks=self.logs_dir/'verification.jsonl'
            rows=[json.loads(line) for line in checks.read_text().splitlines()] if checks.exists() else []
            atomic(self.logs_dir/'enhancement-cost.json',dict(observer_calls=len(rows),observer_wall_sec=sum(x['wall_sec'] for x in rows),
                additional_model_calls=0,additional_model_tokens=0,repair_calls=0))
            atomic(self.root/'terminal.json',{'status':status})
