"""E02-K text-only Windows relay and job-object child supervisor."""
import ctypes as c
from ctypes import wintypes as w
import json,os,re,shutil,subprocess as s,sys,time
from pathlib import Path

def job():
    k=c.WinDLL('kernel32',use_last_error=True)
    def api(name,args,result):
        f=getattr(k,name);f.argtypes=args;f.restype=result;return f
    class Basic(c.Structure):
        _fields_=[('per',c.c_int64),('total',c.c_int64),('flags',w.DWORD),('min',c.c_size_t),('max',c.c_size_t),('active',w.DWORD),('affinity',c.c_size_t),('priority',w.DWORD),('sched',w.DWORD)]
    class Extended(c.Structure):
        _fields_=[('basic',Basic),('io',c.c_uint64*6),('mem',c.c_size_t*4)]
    h=api('CreateJobObjectW',[c.c_void_p,w.LPCWSTR],w.HANDLE)(None,None)
    v=Extended();v.basic.flags=0x2000
    if not h or not api('SetInformationJobObject',[w.HANDLE,c.c_int,c.c_void_p,w.DWORD],w.BOOL)(h,9,c.byref(v),c.sizeof(v)):
        raise c.WinError(c.get_last_error())
    me=api('GetCurrentProcess',[],w.HANDLE)()
    if not api('AssignProcessToJobObject',[w.HANDLE,w.HANDLE],w.BOOL)(h,me):
        raise c.WinError(c.get_last_error())
    # This non-inheritable handle stays open until this supervisor exits.

def supervise(spec):
    job()
    left=float(spec['end'])-time.time()
    if left<=0:return 124
    source=open(spec['input'],'rb') if spec.get('input') else None
    with open(spec['stdout'],'wb') as out,open(spec['stderr'],'wb') as err:
        try:return s.run(spec['argv'],stdin=source if source else s.DEVNULL,stdout=out,stderr=err,timeout=left,creationflags=s.CREATE_NO_WINDOW).returncode
        except s.TimeoutExpired:return 124
        finally:
            if source:source.close()

def write(p,obj):p.write_text(json.dumps(obj),encoding='utf-8')
def launch(specpath,argv,out,err,end,source=None):
    write(specpath,dict(argv=argv,stdout=str(out),stderr=str(err),end=end,input=str(source) if source else None))
    rc=s.run([sys.executable,__file__,'supervise',str(specpath)],timeout=max(.05,end-time.time())+2,creationflags=s.CREATE_NO_WINDOW).returncode
    return rc

def relay(trial,local,end):
    if os.environ.get('GEOTREE_L_RUN_APPROVED')!='EXPLICIT_PAIR_APPROVAL':raise PermissionError('awaiting user approval for L pair')
    if not re.fullmatch(r'l-[0-9a-f]{16}-l[01]',trial):raise ValueError('invalid trial ID')
    local=Path(local).resolve();local.mkdir(exist_ok=False);(local/'minimal').mkdir()
    shutil.copyfile(Path(__file__).with_name('action-schema.json'),local/'schema.json')
    target=os.environ['GEOTREE_RELAY_SSH_TARGET']; base=os.environ['GEOTREE_RELAY_RUN_ROOT'];
    if not re.fullmatch(r'/[a-zA-Z0-9_./-]+',base):raise ValueError('Use a simple POSIX absolute run path')
    root=f'{base}/{trial}/mailbox'
    ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=5',target]
    def remote(command,deadline=end):
        return s.run(ssh+[command],capture_output=True,check=True,timeout=max(.05,min(10,deadline-time.time())),creationflags=s.CREATE_NO_WINDOW).stdout
    try:
        for i in range(4):
            while time.time()<end:
                raw=remote(f'if test -f {root}/terminal.json; then echo TERMINAL; elif test -f {root}/observation-{i}.json; then cat {root}/observation-{i}.json; fi')
                if raw.strip()==b'TERMINAL':write(local/'terminal.json',{'status':'agent_terminal'});return
                if raw:break
                time.sleep(.4)
            else:raise TimeoutError('trial_deadline')
            envelope=json.loads(raw);obs=envelope['observation'];deadline=min(end,envelope['deadline']);model_end=deadline-12
            (local/f'observation-{i}.json').write_bytes(raw)
            prompt=('Public task and current external CAD state follow. Respond once using exact request_id and output schema. '
              'Workspace check already succeeded: begin with run_freecad and a complete script. '
              'Use loops and data tables to keep code concise; no functions or unsupported syntax. '
              'Return done with empty code when your artifact has been created and no evidenced correction is needed. '
              'If revising, provide the entire updated script. No tools or hidden score.\n'+json.dumps(obs,separators=(',',':')))
            (local/f'request-{i}.txt').write_text(prompt,encoding='utf-8')
            response=local/f'response-{i}.json';events=local/f'events-{i}.jsonl'
            argv=[shutil.which('codex'),'exec','--ignore-user-config','--ignore-rules','--ephemeral','--skip-git-repo-check','-s','read-only','-C',str(local/'minimal'),'-m','gpt-6.2-sol']
            for flag in ('shell_tool','unified_exec','multi_agent','skill_search','apps','plugins','remote_plugin','in_app_browser','shell_snapshot','tool_search'):argv+=['--disable',flag]
            argv+=['--enable','skip_host_skill_discovery','-c','project_doc_max_bytes=0','-c','web_search="disabled"','-c','model_reasoning_effort="high"','--output-schema',str(local/'schema.json'),'--json','-o',str(response),'-']
            cfg=['model_provider="geotree_https"',
                 'model_providers.geotree_https.name="GeoTree HTTPS"',
                 'model_providers.geotree_https.base_url="https://chatgpt.com/backend-api/codex"',
                 'model_providers.geotree_https.wire_api="responses"',
                 'model_providers.geotree_https.requires_openai_auth=true',
                 'model_providers.geotree_https.supports_websockets=false',
                 'model_providers.geotree_https.request_max_retries=0',
                 'model_providers.geotree_https.stream_max_retries=0',
                 'model_providers.geotree_https.stream_idle_timeout_ms=480000',
                 'forced_login_method="chatgpt"']
            role=Path(__file__).with_name('cad-role.md')
            if role.is_file():cfg.append('model_instructions_file='+json.dumps(str(role)))
            for c in cfg:argv[-1:-1]=['-c',c]
            write(local/f'request-started-{i}.json',{'model':'gpt-6.2-sol','reasoning_effort':'high','time':time.time()})
            rc=launch(local/f'launch-{i}.json',argv,events,local/f'stderr-{i}.txt',model_end,local/f'request-{i}.txt')
            write(local/f'exit-{i}.json',{'returncode':rc,'time':time.time()})
            if rc or time.time()>=deadline:raise RuntimeError(f'model exit={rc} or deadline expired')
            ev=[json.loads(x) for x in events.read_text(encoding='utf-8-sig').splitlines()]
            if any(e.get('item',{}).get('type') not in ('agent_message','reasoning','error') for e in ev if e.get('item')):raise RuntimeError('unexpected model tool event')
            usage=[e['usage'] for e in ev if e.get('type')=='turn.completed'][-1]
            write(local/f'usage-{i}.json',usage)
            a=json.loads(response.read_text(encoding='utf-8-sig'))
            if set(a)!={'request_id','action','code','reason'} or a.get('request_id')!=obs['request_id'] or a['action'] not in obs['allowed_actions']:raise ValueError('invalid action schema or stale ID')
            reply=local/f'action-{i}.json';write(reply,dict(action=a,usage=usage))
            s.run(['scp','-q',str(reply),f'{target}:{root}/action-{i}.tmp'],check=True,timeout=max(.05,min(10,deadline-time.time())),creationflags=s.CREATE_NO_WINDOW)
            if time.time()>=deadline:raise TimeoutError('late response')
            remote(f'test ! -f {root}/terminal.json && mv {root}/action-{i}.tmp {root}/action-{i}.json',deadline)
        write(local/'terminal.json',{'status':'decision_limit'})
    except Exception as e:
        write(local/'relay-error.json',{'error':type(e).__name__,'detail':str(e)})
        try:s.run(['scp','-q',str(local/'relay-error.json'),f'{target}:{root}/relay-error.json'],timeout=5,check=False,creationflags=s.CREATE_NO_WINDOW)
        finally:raise

if __name__=='__main__':
    if sys.argv[1]=='supervise':sys.exit(supervise(json.loads(Path(sys.argv[2]).read_text())))
    relay(sys.argv[1],sys.argv[2],float(sys.argv[3]))
