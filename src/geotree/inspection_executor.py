"""Offline continuation executor: never runs model code; mounts only approved files."""
from dataclasses import asdict
from pathlib import Path
import hashlib,json,subprocess,time,os
from .active_geometry import validate_query

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

class InspectionExecutor:
    def __init__(self, artifact: Path, source: Path, worker: Path, catalogue: dict, image: str, model_source: Path):
        self.artifact,self.source,self.worker,self.catalogue,self.image,self.model_source=artifact,source,worker,catalogue,image,model_source
        self.frozen=sha(artifact)
        self.source_sha=sha(source)
    def execute(self,packet):
        q=validate_query(packet,self.catalogue);before=sha(self.artifact)
        if self.artifact.is_symlink() or before!=self.frozen or self.source.is_symlink() or sha(self.source)!=self.source_sha:
            raise ValueError("frozen input changed")
        cmd=['docker','run','--rm','--pull','never','--network','none','--cpus','2','--memory','4g','--pids-limit','128',
             '--user','65534:65534','--cap-drop','ALL','--security-opt','no-new-privileges','--read-only',
             '--tmpfs','/tmp:rw,nosuid,nodev,size=64m,mode=1777','--entrypoint','/usr/bin/timeout',
             '-e','HOME=/tmp','-e','OMP_NUM_THREADS=1','-e','OPENBLAS_NUM_THREADS=1',
             '-e','E03_QUERY='+json.dumps(asdict(q)),'-e','E03_ARTIFACT_SHA256='+before,'-e','E03_INSTRUCTION_SHA256='+self.source_sha]
        for path,dest in [(self.artifact,'/in/answer.FCStd'),(self.source,'/in/instruction.md'),
                          (self.worker,'/opt/geotree/worker.py'),(self.model_source,'/opt/geotree/active_geometry.py')]:
            if not path.is_file() or path.is_symlink():raise ValueError("invalid approved mount")
            cmd+=['--mount',f'type=bind,source={path.resolve()},target={dest},readonly']
        cmd += [self.image,'--signal=KILL','20s','/opt/conda/bin/python','-I','/opt/geotree/worker.py']
        start=time.monotonic()
        try:r=subprocess.run(cmd,capture_output=True,text=True,timeout=26,check=False)
        except subprocess.TimeoutExpired:return self.unknown(q,before,start,"worker_timeout")
        if sha(self.artifact)!=before:raise ValueError("historical artifact changed")
        rows=[x.removeprefix('E03_RESULT=') for x in r.stdout.splitlines() if x.startswith('E03_RESULT=')]
        if r.returncode or len(rows)!=1:return self.unknown(q,before,start,"worker_exit_or_protocol",r.returncode,r.stderr[-3000:])
        x=json.loads(rows[0])
        if x["artifact_sha256"]!=before or x["query"]!=asdict(q):raise ValueError("worker binding")
        return x|dict(wall_seconds=time.monotonic()-start,exit_status=r.returncode)
    @staticmethod
    def unknown(q,sha,start,reason,exit_status=None,stderr=None):
        return dict(query=asdict(q),status="UNKNOWN",unique_mapping=False,measured=None,artifact_sha256=sha,
          reason=reason,wall_seconds=time.monotonic()-start,exit_status=exit_status,stderr=stderr)
