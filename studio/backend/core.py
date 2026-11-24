from pathlib import Path
import os,json,hashlib,subprocess,shutil
from geotree.decision_bridge import validate
ROOT=Path(__file__).resolve().parents[2]
IMAGE=os.getenv('GEOTREE_FREECAD_IMAGE','geotree/freecad:1.1.0')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cad(job,src,tag='artifact',replay=False):
 out=job/tag;out.mkdir(mode=0o700);out.chmod(0o777)
 script=job/('replay-input.py' if replay else 'answer.py')
 script.write_text(src,encoding='utf-8')
 cmd=['docker','run','--rm','--name','geotree-e06-'+job.name+'-'+tag,'--pull','never','--network','none','--cpus','2','--memory','4g',
 '--pids-limit','128','--user','65534:65534','--cap-drop','ALL','--security-opt','no-new-privileges','--read-only',
 '--tmpfs','/tmp:rw,nosuid,nodev,size=64m,mode=1777','--tmpfs','/app:rw,nosuid,nodev,size=128m,mode=1777',
 '-e','HOME=/tmp','-e','QT_QPA_PLATFORM=offscreen','-e','OMP_NUM_THREADS=1','-e','OPENBLAS_NUM_THREADS=1']
 for p,t,mode in [(script,'/in/answer.py','readonly'),(ROOT/'studio/backend/snapshot.py','/in/snapshot.py','readonly'),(out,'/out','')]:
  cmd+=['--mount',f'type=bind,source={p},target={t}'+(','+mode if mode else '')]
 cmd+=['--workdir','/app','--entrypoint','/bin/bash',IMAGE,'-ec',
 'cp /in/answer.py /app/answer.py; timeout -k 2 60 '+('freecadcmd /app/answer.py </dev/null' if replay else '/opt/conda/bin/python -I /app/answer.py')+
 '; test -s /app/answer.FCStd; timeout -k 2 35 /opt/conda/bin/python -I /in/snapshot.py; cp /app/answer.FCStd /out/answer.FCStd']
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=110);(job/(tag+'.log')).write_text(r.stdout+'\n'+r.stderr)
 if r.returncode:raise ValueError('FreeCAD exit '+str(r.returncode)+': '+r.stderr[-1500:])
 m=json.loads((out/'steps.json').read_text())
 if sha(out/'answer.FCStd')!=m['artifact_sha256']:raise ValueError('SHA mismatch')
 return m

def preview_existing(source,out):
 out.mkdir();out.chmod(0o777)
 cmd=['docker','run','--rm','--pull','never','--network','none','--cpus','2','--memory','4g','--pids-limit','128',
      '--user','65534:65534','--cap-drop','ALL','--security-opt','no-new-privileges','--read-only',
      '--tmpfs','/tmp:rw,nosuid,nodev,size=64m,mode=1777','-e','HOME=/tmp','-e','OMP_NUM_THREADS=1']
 for p,d in [(source,'/app/answer.FCStd'),(ROOT/'studio/backend/snapshot.py','/in/snapshot.py'),(out,'/out')]:
  cmd+=['--mount',f'type=bind,source={p.resolve()},target={d}'+('' if d=='/out' else ',readonly')]
 r=subprocess.run(cmd+['--entrypoint','/usr/bin/timeout',IMAGE,'35s','/opt/conda/bin/python','-I','/in/snapshot.py'],capture_output=True,text=True,timeout=42)
 (out/'mesh.log').write_text(r.stdout+'\n'+r.stderr)
 if r.returncode:raise ValueError('Preview export failed: '+r.stderr[-1500:])
 m=json.loads((out/'steps.json').read_text())
 if sha(source)!=m['artifact_sha256']:raise ValueError('Preview SHA mismatch')
 return m
