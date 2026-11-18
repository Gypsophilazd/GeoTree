import asyncio,json,tempfile
from pathlib import Path
from harbor.environments.base import ExecResult
from harbor.models.trajectories import Trajectory
from geotree.nosearch import *
class Env:
 def __init__(self,timeout=False):self.timeout=timeout;self.calls=0
 async def exec(self,*args,**kwargs):
  self.calls+=1
  if self.timeout:raise TimeoutError('fixture timeout')
  return ExecResult(return_code=0,stdout=None,stderr=None)
class BadProvider:
 async def propose(self,obs):return ModelReply({'unexpected':'bad'}, {})
async def main():
 with tempfile.TemporaryDirectory() as name:
  root=Path(name)
  async def run(label,provider,env,budget=3):
   rec=FeedbackRecorder(root/label);status=await NoSearchRuntime(provider,Executor(env,rec.path),rec,budget).run('offline fixture');Trajectory.model_validate_json((rec.path/'trajectory.json').read_text());return status
  env=Env();p=MockProvider(['check_workspace','done']);assert await run('nullable',p,env)=='done';assert p.observations[1]['history'][0]['stdout']=='';assert env.calls==1
  print('PASS nullable stdout/stderr, feedback -> next decision, ATIF')
  env=Env();p=MockProvider(['ssh','check_workspace','done']);assert await run('reject',p,env)=='done';assert p.observations[1]['history'][0]['status']=='rejected';assert env.calls==1
  print('PASS rejected action feedback and no rejected execution')
  p=MockProvider(['check_workspace','done']);await run('timeout',p,Env(True));assert p.observations[1]['history'][0]['status']=='timeout';print('PASS tool timeout feedback')
  env=Env();assert await run('malformed',BadProvider(),env,2)=='budget_exhausted';assert env.calls==0;print('PASS illegal model payload and maximum budget')
  p=MockProvider(['check_workspace']*3);env=Env();assert await run('budget',p,env,2)=='budget_exhausted';assert env.calls==2;print('PASS no action beyond budget')
  async def transport(obs):return {'action':dict(request_id=obs['request_id'],action='done',code='',reason='transport fixture'),'usage':{'input_tokens':1}}
  assert await run('replaceable',JSONTransportProvider(transport),Env())=='done';print('PASS replaceable JSON transport without Codex')
  mailbox=root/'mb';m=CodexMailboxProvider(mailbox,.01)
  try:await m.propose({'turn':0})
  except TimeoutError:pass
  else:raise AssertionError('timeout required')
  (mailbox/'relay-error.json').write_text('{}')
  try:await m.propose({'turn':1})
  except RuntimeError:pass
  else:raise AssertionError('relay error required')
  print('PASS relay timeout/error signals')
  import geotree.nosearch_agent as adapter
  adapter.ROOT=root/'adapter';a=adapter.GeoTreeNoSearchAgent(root/'adapterlogs');env=Env();await a.setup(env)
  try:await a.run('fixture',env,None)
  except AttributeError:pass
  assert json.loads((adapter.ROOT/'terminal.json').read_text())['status']=='error';print('PASS adapter exceptional termination signal')
  # Normal termination marker using a pre-seeded done response via mock runtime.
  original=adapter.NoSearchRuntime
  class Runtime:
   def __init__(self,*a,**k):pass
   async def run(self,*a):return 'done'
  class GoodEnv(Env):
   async def download_file(self,*args):pass
  adapter.NoSearchRuntime=Runtime
  await a.run('fixture',GoodEnv(),None)
  assert json.loads((adapter.ROOT/'terminal.json').read_text())['status']=='done';adapter.NoSearchRuntime=original
  print('PASS adapter normal termination signal')
  from geotree.decision_bridge import validate
  for code in ['import os','open("/etc/passwd")','import FreeCAD\nFreeCAD.openDocument("/hidden")']:
   try:validate(dict(request_id='x',action='run_freecad',code=code,reason='test'),'x')
   except ValueError:pass
   else:raise AssertionError('boundary rejection')
  print('PASS basic code rejection; NOT a Python sandbox proof')
asyncio.run(main())
