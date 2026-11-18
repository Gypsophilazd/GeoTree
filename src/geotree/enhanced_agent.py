"""E02-K paired text entry. Only K1 emits evidence-gated post-action feedback."""
import hashlib,json,os,re,time
from pathlib import Path
from geotree.paths import runtime_dir
from harbor.agents.base import BaseAgent
from harbor.agents.capabilities import AgentCapabilities
from geotree.paired_agent import Budget,Mailbox,Executor,Runtime,atomic
from geotree.nosearch import FeedbackRecorder

ROOT=(runtime_dir()/'k')
INSTRUCTION_SHA='748281ae72fccb4316490b016b5b6b55b776da176b9757cb9ef2a8c3f931960e'
MODULES=('constraint_candidates','evidence_gate','geometry_observer','task_geometry','safe_repair','verification_harness')
WORKER='''import sys
sys.path.insert(0,"/opt/geotree-k")
from geotree.k_worker import main
main()
'''

def digest_bytes(b):return hashlib.sha256(b).hexdigest()
def log(path,obj):
    with path.open('a') as f:f.write(json.dumps(obj,allow_nan=False)+'\n')

class TextExecutor(Executor):
    async def execute(self,p):
        if p.action!='check_workspace':return await super().execute(p)
        t=time.monotonic()
        cmd="test -d /app && test -w /app && printf 'text_workspace_ok\\n'"
        r=await self.budget.bound(lambda:self.env.exec(cmd,cwd='/app',timeout_sec=10,user='65534'),10)
        return dict(status='executed',command=cmd,exit_status=r.return_code,stdout=r.stdout or '',stderr=r.stderr or '',elapsed_sec=time.monotonic()-t)

class EnhancedFeedback:
    def __init__(self,base,env,logs,budget,public_sha):
        self.base=base;self.env=env;self.logs=logs;self.budget=budget;self.public_sha=public_sha
    async def execute(self,p):
        raw=await self.base.execute(p)
        if p.action!='run_freecad' or raw.get('exit_status')!=0:return raw
        limit=min(10,self.budget.remaining()-.1)
        if limit<1:return raw|{'task_grounded':{'status':'NOT_RUN','reason':'trial_deadline'}}
        cmd=f'exec timeout --signal=KILL {limit:.3f}s env HOME=/tmp/geotree-home OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /opt/conda/bin/python -I /opt/geotree-k/worker.py'
        t=time.monotonic()
        record=dict(action_id=p.request_id,command=cmd,observer_calls=1,repair_calls=0,model_calls=0)
        try:
            r=await self.budget.bound(lambda:self.env.exec(cmd,cwd='/app',timeout_sec=12,user='65534'),12)
            record.update(exit_status=r.return_code,stdout=r.stdout or '',stderr=r.stderr or '')
            if r.return_code:raise RuntimeError('worker_exit')
            lines=[s.partition('=')[2] for s in (r.stdout or '').splitlines() if s.startswith('GEOTREE_K=')]
            if len(lines)!=1 or len(lines[0])>160000:raise ValueError('worker_protocol')
            data=json.loads(lines[0]);report=data['report'];rows=report['results']
            if data['public_sha256']!=self.public_sha or any(x['public_sha256']!=self.public_sha or x['artifact_sha256']!=report['artifact_sha256'] for x in rows):
                raise ValueError('worker_binding')
            counts={s:sum(x['status']==s for x in rows) for s in ('PASS','FAIL','UNKNOWN','NOT_CHECKABLE')}
            details=[dict(id=x['candidate']['constraint_id'],expected=x['candidate']['expected_value'],measured=x['measured'],
               unit=x['candidate']['unit'],status=x['status'],reason=x['reason'],source=x['candidate']['source_text']) for x in rows if x['status']!='NOT_CHECKABLE']
            return raw|{'task_grounded':dict(status=report['artifact_status'],action_id=p.request_id,artifact_sha256=report['artifact_sha256'],
                counts=counts,checks=details,disposition=data['disposition'],repair=data['repair'],wall_sec=time.monotonic()-t)}
        except (TimeoutError,ValueError,RuntimeError,KeyError,TypeError) as e:
            record.update(error=type(e).__name__,reason=str(e))
            return raw|{'task_grounded':dict(status='ERROR',reason=type(e).__name__,action_id=p.request_id)}
        finally:
            record['wall_sec']=time.monotonic()-t;log(self.logs/'verification.jsonl',record)

class EnhancedAgent(BaseAgent):
    capabilities=AgentCapabilities(atif=True)
    @staticmethod
    def name():return 'geotree-enhanced-k'
    def version(self):return '0.1.0'
    async def setup(self, environment) -> None:
        trial=os.environ['GEOTREE_K_TRIAL']
        if not re.fullmatch(r'k-[0-9a-f]{16}-k[01]',trial) or self.model_name:raise ValueError('bad K configuration')
        self.root=ROOT/trial/'mailbox'
        self.root.mkdir(mode=0o700,parents=False,exist_ok=False)
        self.logs_dir.mkdir(parents=True,exist_ok=True)
        self.budget=Budget(float(os.environ['GEOTREE_K_DEADLINE']))
        self.enabled=trial.endswith('-k1')
        async def install():
            r=await environment.exec('install -d -o 65534 -g 65534 -m 700 /tmp/geotree-home && chown 65534:65534 /app && chmod 700 /logs && install -d -o root -g root -m 755 /opt/geotree-k/geotree && command -v timeout && test -x /opt/conda/bin/python',timeout_sec=10)
            if r.return_code:raise RuntimeError('setup_failed')
            p=self.logs_dir/'worker-entry.py';p.write_text(WORKER)
            await environment.upload_file(p,'/opt/geotree-k/worker.py')
            for name in (*MODULES,'k_worker'):
                await environment.upload_file(Path(__file__).with_name(name+'.py'),f'/opt/geotree-k/geotree/{name}.py')
            r=await environment.exec('chown -R root:root /opt/geotree-k && chmod 444 /opt/geotree-k/*.py /opt/geotree-k/geotree/*.py',timeout_sec=10)
            if r.return_code:raise RuntimeError('trusted_worker_setup')
            r=await environment.exec('test ! -x /logs && test ! -r /logs/verifier && test ! -S /var/run/docker.sock && test ! -w /opt/geotree-k/geotree && test ! -w /opt/geotree-k/geotree/k_worker.py',user='65534',timeout_sec=5)
            if r.return_code:raise RuntimeError('execution_boundary')
        await self.budget.bound(install,40)
    async def run(self, instruction, environment, context) -> None:
        status='error'
        try:
            configured=os.environ.get('GEOTREE_PUBLIC_INSTRUCTION')
            pinned=os.environ.get('GEOTREE_INSTRUCTION_SHA256')
            if bool(configured)!=bool(pinned):raise ValueError('instruction_path_and_hash_required')
            frozen=(Path(configured) if configured else (ROOT.parent/'e02-j/public/text_create/instruction.md')).read_bytes()
            if digest_bytes(frozen)!=(pinned or INSTRUCTION_SHA) or instruction.strip()!=frozen.decode().strip():
                raise ValueError('task_instruction_mismatch')
            # Canonical bytes for both arms. Any trailing line ending is normalized before evidence replay.
            text=frozen.decode().strip()
            p=self.logs_dir/'public-instruction.md';p.write_text(text,encoding='utf-8')
            await self.budget.bound(lambda:environment.upload_file(p,'/opt/geotree-k/instruction.md'),8)
            r=await self.budget.bound(lambda:environment.exec('chown root:root /opt/geotree-k/instruction.md && chmod 444 /opt/geotree-k/instruction.md',timeout_sec=5),7)
            if r.return_code:raise RuntimeError('public_instruction_install')
            ex=TextExecutor(environment,self.logs_dir,self.budget)
            if self.enabled:ex=EnhancedFeedback(ex,environment,self.logs_dir,self.budget,digest_bytes(text.encode()))
            runtime=Runtime(Mailbox(self.root,self.budget),ex,FeedbackRecorder(self.logs_dir),self.budget)
            status=await self.budget.bound(lambda:runtime.run(text),1200)
        finally:
            if context is not None:
                context.metadata={**(context.metadata or {}),'geotree_terminal':status,'geotree_cad_runs':self.budget.cad}
            checks=self.logs_dir/'verification.jsonl'
            rows=[json.loads(line) for line in checks.read_text().splitlines()] if checks.exists() else []
            atomic(self.logs_dir/'enhancement-cost.json',dict(observer_calls=len(rows),observer_wall_sec=sum(x['wall_sec'] for x in rows),
                additional_model_calls=0,additional_model_tokens=0,repair_calls=0))
            atomic(self.root/'terminal.json',{'status':status})
