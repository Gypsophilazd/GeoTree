import json,os,uuid,ast,time,threading,subprocess,sys,re
from pathlib import Path
from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse,JSONResponse
from pydantic import BaseModel
from .core import ROOT,cad,sha,validate,preview_existing
from . import deepseek
app=FastAPI(); DATA=Path(os.getenv('GEOTREE_STUDIO_RUN_DIR',str(ROOT/'.geotree/studio/jobs'))).resolve();DATA.mkdir(parents=True,exist_ok=True);FRONT=ROOT/'studio/frontend'
lock=threading.RLock()
@app.middleware('http')
async def same_origin(request,call_next):
 origin=request.headers.get('origin')
 if request.method=='POST' and origin and origin not in ('http://127.0.0.1:18765','http://localhost:18765','http://127.0.0.1:8765','http://localhost:8765'):
  return JSONResponse({'detail':'cross-origin write disallowed'},status_code=403)
 return await call_next(request)

def jd(i):
 if not re.fullmatch('[a-f0-9]{32}',i) or not (DATA/i).is_dir():raise HTTPException(404)
 return DATA/i
def read(p):return json.loads((p/'state.json').read_text())
def save(p,s):
 tmp=p/'tmp.json';tmp.write_text(json.dumps(s,ensure_ascii=False));tmp.replace(p/'state.json')
def update(p,status=None,event=None,**kw):
 with lock:
  s=read(p)
  if s['status']=='cancelled' and status!='cancelled':return s
  if status:s['status']=status
  s.update(kw)
  if event:
   with (p/'events.jsonl').open('a') as f:f.write(json.dumps(dict(time=time.time(),event=event,status=s['status'],data=kw),default=str,ensure_ascii=False)+'\n')
  save(p,s);return s
PROMPT='Return a JSON CAD action with exact request_id, action=run_freecad, code, reason. No tools. Build a valid single parametric PartDesign Body using distinct named features. Only import FreeCAD, Part, Sketcher, math. No functions, classes, reflection, files or OS; loops allowed. The validator rejects slash characters in string literals except the save path: in FreeCAD expression strings replace division by 2 with multiplication by 0.5. Python arithmetic division outside strings is fine. Save only doc.saveAs("/app/answer.FCStd"). For under-specified obvious dimensions choose and state reasonable assumptions. '
def get_prompt(s):return PROMPT+json.dumps(dict(request_id=s['id'],public_task=s['prompt']),ensure_ascii=False)
def execute(p,a,usage,model):
 try:
  validate(a,p.name)
  if a['action']!='run_freecad':raise ValueError('expected run_freecad')
  update(p,'building','validated_action',reason=a['reason'],usage=usage,model=model)
  if read(p)['status']=='cancelled':return
  m=cad(p,a['code']);update(p,'replaying','features_exported',features=m,sha=m['artifact_sha256'])
  if read(p)['status']=='cancelled':return
  r=cad(p,a['code'],'replay',True)
  same=len(m['steps'])==len(r['steps']) and all((x['name'],x['type'],x['solids'])==(y['name'],y['type'],y['solids']) and abs(x['volume']-y['volume'])<1e-5 and max(abs(a-b) for a,b in zip(x['bounds'],y['bounds']))<1e-5 for x,y in zip(m['steps'],r['steps']))
  update(p,'done' if same else 'failed','independent_freecadcmd_replay',replay='FEATURE_AND_METRIC_MATCH' if same else 'MISMATCH')
 except Exception as e:update(p,'failed','runtime_error',error=str(e))
@app.get('/')
def index():return FileResponse(FRONT/'index.html')
@app.get('/api/providers')
def providers():return {'Codex':'LIVE · requires Windows bridge','DeepSeek Flash':'LIVE' if deepseek.available() else 'NOT_CONFIGURED','Mock':'MOCK · transport only'}
@app.get('/api/jobs')
def jobs():return sorted([read(p) for p in DATA.iterdir() if (p/'state.json').is_file()],key=lambda s:s['created'],reverse=True)
class Input(BaseModel):
 prompt:str
 provider:str
@app.post('/api/jobs')
def create(x:Input):
 if not 1<=len(x.prompt.strip())<=6000 or x.provider not in providers():raise HTTPException(400)
 with lock:
  if x.provider=='Codex' and len([s for s in jobs() if s['provider']=='Codex'])>=int(os.getenv('GEOTREE_STUDIO_CODEX_LIMIT','2')):raise HTTPException(409,'Codex session authorization limit for this run directory')
  if any(s['status'] in ('queued','model','building','replaying') for s in jobs()):raise HTTPException(409,'Only one active run')
  if x.provider=='DeepSeek Flash' and not deepseek.available():raise HTTPException(409,'NOT_CONFIGURED')
  p=DATA/uuid.uuid4().hex;p.mkdir()
  s=dict(id=p.name,prompt=x.prompt,provider=x.provider,mode='MOCK' if x.provider=='Mock' else 'LIVE',created=time.time(),status='queued');save(p,s)
 update(p,event='user_text_received')
 if x.provider=='Mock':update(p,'done','mock_transport_only',note='No CAD or benchmark produced.')
 if x.provider=='DeepSeek Flash':
  def go():
   try:
    update(p,'model','provider_started')
    a,u,m=deepseek.call(get_prompt(s),lambda e,v:update(p,event=e,stream=v))
    execute(p,a,u,m)
   except Exception as e:update(p,'failed','provider_failed',error=str(e))
  threading.Thread(target=go,daemon=True).start()
 return read(p)
@app.get('/api/jobs/{i}')
def get(i:str):
 p=jd(i); f=p/'events.jsonl'
 with lock:return read(p)|{'events':[json.loads(x) for x in f.read_text().splitlines()] if f.exists() else []}
@app.post('/api/jobs/{i}/cancel')
def cancel(i:str):
 p=jd(i)
 old=read(p)['status']
 if old in ('done','failed','cancelled'):return read(p)
 update(p,'cancelled','cancellation_requested')
 if old in ('building','replaying'):
  try:subprocess.run(['docker','stop','--time','1','geotree-e06-'+i+'-'+('artifact' if old=='building' else 'replay')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5)
  except subprocess.TimeoutExpired:pass
 return read(p)
@app.post('/bridge/claim')
def claim():
 with lock:
  for s in jobs():
   if s['provider']=='Codex' and s['status']=='queued':
    update(jd(s['id']),'model','codex_process_claimed')
    return {'id':s['id'],'prompt':get_prompt(s),'attempt':s.get('attempt',1)}
 return {}
@app.post('/bridge/{i}/event')
def event(i:str,packet:dict):
 p=jd(i)
 if read(p)['status']=='model':update(p,event='codex.'+str(packet.get('type','unknown')),provider_event=packet)
 return {}
@app.post('/bridge/{i}/result')
def result(i:str,packet:dict):
 p=jd(i)
 with lock:
  if read(p)['status']!='model':raise HTTPException(409)
  if 'error' in packet:update(p,'failed','codex_failed',error=packet['error']);return {}
  update(p,'building','codex_response_received')
 threading.Thread(target=execute,args=(p,packet['action'],packet.get('usage',{}),packet.get('model','gpt-6.2-sol')),daemon=True).start()
 return {}
@app.get('/api/jobs/{i}/file/{name}')
def file(i:str,name:str):
 p=jd(i)
 if name in ('answer.py','events.jsonl'):f=p/name
 elif re.fullmatch(r'answer\.FCStd|steps\.json|step-[0-9]+\.(json|stl)',name):f=p/'artifact'/name
 else:raise HTTPException(404)
 if not f.is_file():raise HTTPException(404)
 return FileResponse(f,filename=name)
def synthetic_case():
 from . import repair_runner as runner
 d=DATA.parent/'demo'; d.mkdir(parents=True,exist_ok=True)
 c=d/('case-'+uuid.uuid4().hex); c.mkdir()
 for name in ('answer.py','contract.json','instruction.md'):
  (c/name).write_bytes((ROOT/'examples/demo'/name).read_bytes())
 result=runner.run(runner.mounts(c,c/'answer.py'),runner.BUILD+'cp /app/answer.FCStd /out/answer.FCStd',c/'build')
 if result['rc']!=0:raise HTTPException(503,'FreeCAD demo unavailable: check Docker and configured image')
 (c/'answer.FCStd').write_bytes((c/'build/answer.FCStd').read_bytes())
 return c

@app.post('/api/demo/inspect')
def inspect():
 from . import repair_runner as runner
 c=synthetic_case()
 _,data=runner.certify(c)
 return data['before']|{'public_sha256':runner.sha(c/'instruction.md'),'mode':'SYNTHETIC / LIVE READ-ONLY INSPECTION'}

@app.get('/api/benchmark')
def benchmark():return json.loads((ROOT/'configs/benchmark_e06.json').read_text())


@app.post('/api/jobs/{i}/clarify')
def clarify(i:str,x:Input):
 p=jd(i);s=read(p)
 if s['status']!='failed' or s['provider']!='Codex' or s.get('attempt',1)!=1 or (p/'artifact').exists() or not 1<=len(x.prompt.strip())<=6000:
  raise HTTPException(409,'One clarification only, before first CAD execution')
 return update(p,'queued','user_clarification_same_session',prompt=x.prompt,original_prompt=s['prompt'],attempt=2,error=None)

@app.post('/api/demo/repair')
def repair_demo():
 from . import repair_runner as runner
 c=synthetic_case();r=DATA.parent/'demo'/('repair-'+uuid.uuid4().hex)
 data=runner.attempt(c,r,runner.rule(runner.parse_contract(c)),runner.facts(c))|{'evidence_path':r.name,'scope':'E05 SYNTHETIC / LIVE isolated repair'}
 if data['status']=='ACCEPTED':
  data['previews']={}
  for arm,file in [('before',c/'answer.FCStd'),('after',r/'accepted/answer.FCStd')]:
   m=preview_existing(file,r/('mesh-'+arm));t=m['steps'][-1]
   data['previews'][arm]=t|{'url':'/api/demo/repair-mesh/'+r.name+'/'+arm+'/'+t['mesh'],'sha':m['artifact_sha256']}
 return data

@app.get('/api/demo/repair-mesh/{i}/{arm}/{name}')
def repair_mesh(i:str,arm:str,name:str):
 if not re.fullmatch(r'repair-[a-f0-9]{32}',i) or arm not in ('before','after') or not re.fullmatch(r'step-[0-9]+\.json',name):raise HTTPException(404)
 p=DATA.parent/'demo'/i/('mesh-'+arm)/name
 if not p.is_file():raise HTTPException(404)
 return FileResponse(p)


@app.get('/api/jobs/{i}/occ')
def verified_evidence(i:str):
 p=jd(i);ev=p/'occ-evidence.json'
 if not ev.is_file():raise HTTPException(404,'No separate OCC evidence archived for this job')
 x=json.loads(ev.read_text())
 if x['artifact_sha256']!=sha(p/'artifact/answer.FCStd'):raise HTTPException(409,'Artifact changed since measurement')
 return x|{'mode':'STORED INDEPENDENT OCC EVIDENCE'}

@app.get('/api/benchmark/export/{name}')
def benchmark_export(name:str):
 if name not in ('benchmark_results.csv','benchmark_results.json','benchmark_chart.svg','benchmark_chart.png'):
  raise HTTPException(404)
 p=ROOT/'docs/presentation'/name
 if not p.is_file():raise HTTPException(404)
 return FileResponse(p,filename=name)
