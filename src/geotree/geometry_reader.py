"""Trusted fixed-path reader. Install root-owned payload before untrusted actions."""
import asyncio,json,time
from pathlib import Path
from geotree.geometry_observer import GeometryObservation
COMMAND='HOME=/tmp/geotree-home OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /opt/conda/bin/python -I /opt/geotree-observer/reader.py'
PAYLOAD='''import sys,json
sys.path.insert(0,"/opt/geotree-observer")
from geometry_observer import inspect_file
print("GEOTREE_OBSERVATION="+json.dumps(inspect_file("/app/answer.FCStd","/app").to_dict(),allow_nan=False))
'''
class FixedGeometryReader:
    def __init__(self,environment,logs_dir):self.environment=environment;self.logs_dir=Path(logs_dir);self.action_id=None
    async def setup(self):
        self.logs_dir.mkdir(parents=True,exist_ok=True)
        r=await self.environment.exec('install -d -o root -g root -m 755 /opt/geotree-observer',timeout_sec=10)
        if r.return_code:raise RuntimeError('observer trusted directory setup failed')
        source=self.logs_dir/'reader-payload.py';source.write_text(PAYLOAD)
        await self.environment.upload_file(source,'/opt/geotree-observer/reader.py')
        await self.environment.upload_file(Path(__file__).with_name('geometry_observer.py'),'/opt/geotree-observer/geometry_observer.py')
        r=await self.environment.exec('chown root:root /opt/geotree-observer/*.py && chmod 444 /opt/geotree-observer/*.py',timeout_sec=10)
        if r.return_code:raise RuntimeError('observer payload protection failed')
    async def __call__(self):
        started=time.time()
        r=await asyncio.wait_for(self.environment.exec(COMMAND,cwd='/app',user='65534',timeout_sec=10),12)
        evidence={'action_id':self.action_id,'observed_at_unix':started,'exit_status':r.return_code,'stdout':r.stdout or '', 'stderr':r.stderr or ''}
        with (self.logs_dir/'observer-reader.jsonl').open('a') as f:f.write(json.dumps(evidence)+'\n')
        if r.return_code:raise RuntimeError('observer command failed; see observer-reader.jsonl')
        lines=[x for x in (r.stdout or '').splitlines() if x.startswith('GEOTREE_OBSERVATION=')]
        if len(lines)!=1:raise ValueError('missing or ambiguous observer output')
        o=GeometryObservation(**json.loads(lines[0].split('=',1)[1]))
        if len(o.metadata.get('artifact_sha256',''))!=64:raise ValueError('missing artifact SHA256')
        o.metadata.update(action_id=self.action_id,observed_at_unix=started)
        return o
