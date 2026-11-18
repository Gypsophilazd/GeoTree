"""Provider-independent sequential decision loop. No benchmark scorer feedback."""
import asyncio
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Protocol
from uuid import uuid4
from harbor.models.trajectories import Agent, Step, Trajectory
from geotree.decision_bridge import validate

@dataclass(frozen=True)
class ActionProposal:
    request_id: str
    action: str
    code: str
    reason: str

@dataclass
class ModelReply:
    payload: dict
    usage: dict

class ModelProvider(Protocol):
    async def propose(self, observation: dict) -> ModelReply: ...

class ObservationBuilder:
    def build(self, instruction, history, turn, budget):
        return dict(request_id=str(uuid4()),turn=turn,instruction=instruction,history=list(history),remaining_steps=budget-turn,allowed_actions=['check_workspace','run_freecad','done'],script_policy='Straight-line Python only: import FreeCAD, Part, Sketcher, math; no def/class/with/try/lambda, reflection, filesystem or network APIs. Save only doc.saveAs("/app/answer.FCStd"). Use named PartDesign features, not baked Part::Feature. No dunder names. Script max 24000 chars. A rejection consumes one decision; use returned error to correct within remaining budget.')

class ActionValidator:
    def check(self, payload, observation):
        if observation['remaining_steps']<=0: raise ValueError('budget exhausted')
        validate(payload,observation['request_id'])
        return ActionProposal(**payload)

class NoSearch:
    k=1
    def select(self, proposals):
        if len(proposals)!=1: raise ValueError('NoSearch requires exactly one candidate')
        return proposals[0]

class Executor:
    def __init__(self, environment, logs_dir): self.environment=environment;self.logs_dir=Path(logs_dir)
    async def execute(self, proposal):
        if proposal.action=='check_workspace':
            command="test -d /app && test -f /app/6b54209a13.png && printf 'workspace_and_drawing_ok\\n'"
        elif proposal.action=='run_freecad':
            guard=await self.environment.exec('test ! -L /app/answer.py && test ! -L /app/answer.FCStd',cwd='/app',timeout_sec=10)
            if guard.return_code: raise ValueError('symlink output rejected')
            source=self.logs_dir/f'{proposal.request_id}.py';source.write_text(proposal.code)
            await self.environment.upload_file(source,'/app/answer.py')
            command='HOME=/tmp/geotree-home OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /opt/conda/bin/python /app/answer.py'
        else: raise ValueError('non-executable action')
        start=time.monotonic()
        result=await asyncio.wait_for(self.environment.exec(command,cwd='/app',timeout_sec=60,user='65534'),timeout=65)
        return dict(status='executed',command=command,exit_status=result.return_code,stdout=(result.stdout or '')[:12000],stderr=(result.stderr or '')[:12000],elapsed_sec=time.monotonic()-start)

class FeedbackRecorder:
    def __init__(self, path):
        self.path=Path(path);self.path.mkdir(parents=True,exist_ok=True);self.steps=[];self.session=str(uuid4())
    def record(self, event, data):
        with (self.path/'trace.jsonl').open('a') as f:f.write(json.dumps(dict(time=time.time(),event=event,data=data))+'\n')
    def step(self, action, feedback):
        i=len(self.steps)+1
        self.steps.append(Step.model_validate(dict(step_id=i,source='agent',message=json.dumps({'proposal':action,'feedback':feedback}),llm_call_count=1)))
        tr=Trajectory(schema_version='ATIF-v1.8',session_id=self.session,agent=Agent(name='geotree-nosearch-dev',version='0.1.0'),steps=self.steps)
        (self.path/'trajectory.json').write_text(tr.model_dump_json(exclude_none=True,indent=2))

class NoSearchRuntime:
    def __init__(self,provider,executor,recorder,max_steps=4):
        self.provider=provider;self.executor=executor;self.recorder=recorder;self.max_steps=max_steps
        self.builder=ObservationBuilder();self.validator=ActionValidator();self.policy=NoSearch()
    async def run(self,instruction):
        history=[];status='budget_exhausted'
        try:
            for turn in range(self.max_steps):
                obs=self.builder.build(instruction,history,turn,self.max_steps);self.recorder.record('observation',obs)
                payload=None
                try:
                    reply=await self.provider.propose(obs);payload=reply.payload
                    self.recorder.record('model_reply',{'payload':payload,'usage':reply.usage})
                    proposal=self.policy.select([self.validator.check(payload,obs)])
                except (ValueError,TypeError,SyntaxError,KeyError) as e:
                    feedback=dict(status='rejected',error=str(e));history.append(feedback);self.recorder.record('feedback',feedback);self.recorder.step(payload,feedback);continue
                if proposal.action=='done':
                    feedback={'status':'done'};self.recorder.step(payload,feedback);status='done';break
                try: feedback=await self.executor.execute(proposal)
                except (TimeoutError,asyncio.TimeoutError): feedback=dict(status='timeout',error='tool execution timeout')
                except Exception as e: feedback=dict(status='execution_error',error=f'{type(e).__name__}: {e}')
                history.append(feedback);self.recorder.record('feedback',feedback);self.recorder.step(payload,feedback)
        except Exception as e:
            status='provider_or_runtime_error';self.recorder.record('fatal',{'type':type(e).__name__,'message':str(e)})
            raise
        finally: self.recorder.record('terminal',{'status':status,'decisions':len(self.recorder.steps)})
        return status

class MockProvider:
    def __init__(self,actions):self.actions=iter(actions);self.observations=[]
    async def propose(self,observation):
        self.observations.append(observation)
        a=next(self.actions)
        if isinstance(a,Exception):raise a
        return ModelReply(dict(request_id=observation['request_id'],action=a,code='',reason='mock fixture'),{})

class JSONTransportProvider:
    """Inject a provider transport; future DeepSeek API plugs in here without loop changes."""
    def __init__(self,transport):self.transport=transport
    async def propose(self,observation):
        raw=await self.transport(observation)
        return ModelReply(raw['action'],raw.get('usage',{}))

class CodexMailboxProvider:
    def __init__(self,root,timeout=420):self.root=Path(root);self.timeout=timeout;self.root.mkdir(parents=True,exist_ok=True)
    async def propose(self,observation):
        i=observation['turn'];p=self.root/f'observation-{i}.json';temp=p.with_suffix('.tmp');temp.write_text(json.dumps(observation));temp.replace(p)
        dest=self.root/f'action-{i}.json';deadline=time.monotonic()+self.timeout
        while not dest.exists():
            if (self.root/'relay-error.json').exists():raise RuntimeError('relay reported failure')
            if time.monotonic()>deadline:raise TimeoutError('model decision timeout')
            await asyncio.sleep(.2)
        if dest.stat().st_size>30000:raise ValueError('response too large')
        payload=json.loads(dest.read_text(encoding='utf-8-sig'))
        usage_file=self.root/f'usage-{i}.json'
        usage=json.loads(usage_file.read_text(encoding='utf-8-sig')) if usage_file.exists() else {}
        return ModelReply(payload,usage)
