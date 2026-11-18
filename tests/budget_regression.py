import asyncio,json,tempfile,time
from pathlib import Path
from geotree.paired_agent import Budget,Runtime,FeedbackRecorder,Mailbox
from harbor.models.trajectories import Trajectory
class Provider:
 def __init__(self,act='check_workspace',usage=1,wrong=False):self.act=act;self.n=0;self.u=usage;self.wrong=wrong
 async def propose(self,o):
  self.n+=1
  return dict(request_id='stale' if self.wrong else o['request_id'],action=self.act,code='',reason='test'),dict(input_tokens=self.u,output_tokens=2)
class Exec:
 def __init__(self,b):self.b=b;self.n=0
 async def execute(self,p):
  self.n+=1
  if p.action=='run_freecad':self.b.cad+=1
  return dict(status='executed',exit_status=0)
async def check(p,want,count,cad=0,delay=4):
 with tempfile.TemporaryDirectory() as d:
  b=Budget(time.time()+delay);e=Exec(b);r=FeedbackRecorder(d)
  assert await Runtime(p,e,r,b).run('fixture')==want
  t=json.loads((Path(d)/'trace.jsonl').read_text().splitlines()[-1])['data']
  assert t['decisions']==count and t['cad_runs']==cad
  if r.steps:Trajectory.model_validate_json((Path(d)/'trajectory.json').read_text())
  return t
async def main():
 await check(Provider(),'decision_budget_exhausted',4)
 await check(Provider('run_freecad'),'cad_budget_exhausted',3,2)
 await check(Provider(wrong=True),'decision_budget_exhausted',4)
 t=await check(Provider(usage=200000),'token_soft_budget',1);assert t['overshoot']==2
 with tempfile.TemporaryDirectory() as d:
  b=Budget(time.time()+.06);m=Mailbox(Path(d),b)
  try:await b.bound(lambda:m.propose({'turn':0}),420)
  except TimeoutError:pass
  else:raise AssertionError('deadline not enforced')
  e=json.loads((Path(d)/'observation-0.json').read_text());assert e['deadline']==b.end
 b=Budget(time.time()+2)
 try:await b.bound(lambda:asyncio.sleep(1),.02)
 except TimeoutError:pass
 else:raise AssertionError('single deadline not enforced')
 print('PASS decision 4, CAD 2, stale ID, soft overshoot, ATIF, single and total deadlines')
asyncio.run(main())
