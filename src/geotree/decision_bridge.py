"""Development-only file mailbox bridge. No model credentials in task environment."""
import ast
import asyncio
import json
import time
from pathlib import Path
from geotree.paths import runtime_dir
from uuid import uuid4
from harbor.agents.base import BaseAgent

ROOT = (runtime_dir()/'legacy-decision/mailbox')
MODULES = {'FreeCAD', 'Part', 'Sketcher', 'math'}
DENIED = {'open','exec','eval','compile','getattr','setattr','delattr','globals','locals','vars','input','help','breakpoint','type','object','super','memoryview','__import__'}

def validate(a, request_id):
    if not isinstance(a,dict) or set(a) != {'request_id','action','code','reason'}:
        raise ValueError('exact action fields required')
    if not all(isinstance(v,str) for v in a.values()): raise ValueError('strings required')
    if a['request_id'] != request_id: raise ValueError('request mismatch')
    if a['action'] not in {'check_workspace','run_freecad','done'}: raise ValueError('action not allowed')
    if len(a['code'])>24000 or len(a['reason'])>2000: raise ValueError('size budget')
    if a['action']!='run_freecad':
        if a['code']: raise ValueError('unexpected code')
        return
    tree=ast.parse(a['code'])
    for n in ast.walk(tree):
        if isinstance(n,(ast.ImportFrom,ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef,ast.With,ast.AsyncWith,ast.Try,ast.Lambda)):
            raise ValueError('unsupported syntax')
        if isinstance(n,ast.Import) and any(x.name not in MODULES for x in n.names): raise ValueError('import not allowed')
        if isinstance(n,ast.Name) and (n.id in DENIED or n.id.startswith('_')): raise ValueError('name not allowed')
        if isinstance(n,ast.Attribute) and (n.attr.startswith('_') or n.attr in {'openDocument','open','loadFile','exec','execfile','getHomePath','getResourceDir','getUserAppDataDir','ParamGet','addImportType','addExportType'}): raise ValueError('attribute not allowed')
        if isinstance(n,ast.Constant) and isinstance(n.value,str) and ('..' in n.value or '\\' in n.value or ('/' in n.value and n.value!='/app/answer.FCStd')): raise ValueError('path string not allowed')
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in {'save','saveAs','export','importBrep','read','write','restore'}:
            if n.func.attr!='saveAs' or len(n.args)!=1 or not isinstance(n.args[0],ast.Constant) or n.args[0].value!='/app/answer.FCStd': raise ValueError('file operation not allowed')

class DecisionBridgeAgent(BaseAgent):
    @staticmethod
    def name(): return 'geotree-decision-bridge-dev'
    def version(self): return '0.1.0'
    async def setup(self,environment):
        if self.model_name: raise ValueError('model runs in trusted Windows process only')
        ROOT.mkdir(parents=True,exist_ok=True)
        self.logs_dir.mkdir(parents=True,exist_ok=True)
    async def run(self,instruction,environment,context):
        # Only this fixed public task input is exported; no task archive or verifier data.
        await environment.download_file('/app/6b54209a13.png',ROOT/'drawing.png')
        history=[]
        for turn in range(4):
            rid=str(uuid4())
            obs={'request_id':rid,'turn':turn,'instruction':instruction,'history':history,'remaining_steps':4-turn,'allowed_actions':['check_workspace','run_freecad','done'],'script_policy':'imports FreeCAD,Part,Sketcher,math only; no reflection/host/filesystem tools; saveAs only /app/answer.FCStd; execute via fixed /opt/conda/bin/python /app/answer.py'}
            (ROOT/f'observation-{turn}.json').write_text(json.dumps(obs))
            self._log('observation',obs)
            dest=ROOT/f'action-{turn}.json'
            deadline=time.monotonic()+300
            while not dest.exists():
                if time.monotonic()>deadline: raise TimeoutError('Windows decision timeout')
                await asyncio.sleep(1)
            if dest.stat().st_size>30000: raise ValueError('message too large')
            a=json.loads(dest.read_text()); self._log('proposal',a)
            validate(a,rid); self._log('validation',{'accepted':True,'request_id':rid})
            if a['action']=='done': break
            if a['action']=='check_workspace':
                command="test -d /app && test -f /app/6b54209a13.png && printf 'workspace_and_drawing_ok\\n'"
            else:
                # Guard output path before uploading; do not follow attacker-created symlinks.
                guard=await environment.exec('test ! -L /app/answer.py && test ! -L /app/answer.FCStd',cwd='/app',timeout_sec=10)
                if guard.return_code: raise ValueError('symlink output rejected')
                script=self.logs_dir/f'proposal-{turn}.py'; script.write_text(a['code'])
                await environment.upload_file(script,'/app/answer.py')
                command='OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /opt/conda/bin/python /app/answer.py'
            result=await environment.exec(command,cwd='/app',timeout_sec=60)
            feedback={'turn':turn,'command':command,'exit_status':result.return_code,'stdout':(result.stdout or '')[:12000],'stderr':(result.stderr or '')[:12000]}
            history.append(feedback); self._log('execution',feedback)
        self._log('ended',{'steps':len(history)})
    def _log(self,event,data):
        with (self.logs_dir/'bridge-trace.jsonl').open('a') as f: f.write(json.dumps({'time':time.time(),'event':event,'data':data})+'\n')
