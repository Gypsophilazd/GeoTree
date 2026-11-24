"""Bounded Windows subscriber using the proven Codex CLI Job Object and ChatGPT route."""
import json,time,urllib.request,os,subprocess,sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=Path(os.environ.get('GEOTREE_STUDIO_EVIDENCE',str(Path.home()/'.geotree/studio-relay')));ROOT.mkdir(parents=True,exist_ok=True)
URL=os.getenv('GEOTREE_STUDIO_URL','http://127.0.0.1:18765').rstrip('/')
def req(p,x=None):
 q=urllib.request.Request(URL+p,data=json.dumps(x).encode() if x is not None else None,headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(q,timeout=7) as s:return json.load(s)
schema=ROOT/'schema.json'
schema.write_text(json.dumps(dict(type='object',additionalProperties=False,required=['request_id','action','code','reason'],properties={k:{'type':'string'} for k in ('request_id','action','code','reason')})))
argv=json.loads((HERE/'recovery-argv-template.json').read_text())['argv']
argv[0]='codex';argv[argv.index('--output-schema')+1]=str(schema)
argv=[('model_instructions_file='+json.dumps(str(HERE/'cad-role.md'))) if a.startswith('model_instructions_file=') else a for a in argv]
started=time.monotonic()
for turn in range(int(os.environ.get("GEOTREE_BRIDGE_JOBS","2"))):
 while time.monotonic()-started<1800:
  j=req('/bridge/claim',{})
  if j:break
  time.sleep(1)
 else:break
 i=j['id'];p=ROOT/(i if j.get('attempt',1)==1 else i+'-clarified');p.mkdir();(p/'minimal').mkdir()
 prompt=p/'prompt.txt';prompt.write_text(j['prompt'],encoding='utf-8')
 ans=p/'answer.json'; out=p/'events.jsonl';err=p/'stderr.txt'
 a=argv.copy();a[a.index('-C')+1]=str(p/'minimal');a[a.index('-o')+1]=str(ans)
 model_end=time.time()+600
 spec=p/'launch.json';spec.write_text(json.dumps(dict(argv=a,stdout=str(out),stderr=str(err),end=model_end,input=str(prompt))))
 child=subprocess.Popen([sys.executable,str(HERE/'job_relay.py'),'supervise',str(spec)],creationflags=subprocess.CREATE_NO_WINDOW)
 n=0;events=[];cancelled=False
 try:
  while True:
   if out.exists():
    lines=out.read_text(encoding='utf-8-sig',errors='replace').splitlines()
    for line in lines[n:]:
     try:e=json.loads(line)
     except ValueError:break
     n+=1;events.append(e)
     req('/bridge/'+i+'/event',{'type':e.get('type'),'item_type':e.get('item',{}).get('type'),'usage':e.get('usage')})
   cancelled=req('/api/jobs/'+i)['status']=='cancelled'
   if cancelled or child.poll() is not None or time.time()>model_end+2:break
   time.sleep(.7)
 finally:
  if child.poll() is None:child.terminate()
  child.wait(timeout=5)
 result={'rc':child.returncode}
 try:
  if cancelled:continue
  if result.get('rc')!=0:raise ValueError(result.get('error') or 'Codex exit '+str(result.get('rc')))
  if any(e.get('item',{}).get('type') not in ('agent_message','reasoning','error') for e in events if 'item' in e):raise ValueError('Unexpected tool event')
  u=[e['usage'] for e in events if e['type']=='turn.completed'];assert len(u)==1
  req('/bridge/'+i+'/result',{'action':json.loads(ans.read_bytes()),'usage':u[0],'model':'gpt-6.2-sol/high'})
 except Exception as e:req('/bridge/'+i+'/result',{'error':str(e)})
