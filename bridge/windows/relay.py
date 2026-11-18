"""Windows shared-mailbox relay and job-object child supervisor."""
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
    with open(spec['stdout'],'wb') as out,open(spec['stderr'],'wb') as err:
        try:return s.run(spec['argv'],stdin=s.DEVNULL,stdout=out,stderr=err,timeout=left,creationflags=s.CREATE_NO_WINDOW).returncode
        except s.TimeoutExpired:return 124

def write(p,obj):p.write_text(json.dumps(obj),encoding='utf-8')
def launch(specpath,argv,out,err,end):
    write(specpath,dict(argv=argv,stdout=str(out),stderr=str(err),end=end))
    rc=s.run([sys.executable,__file__,'supervise',str(specpath)],timeout=max(.05,end-time.time())+2,creationflags=s.CREATE_NO_WINDOW).returncode
    return rc

def relay(trial,local,end):
    if os.environ.get('GEOTREE_L_RUN_APPROVED')!='EXPLICIT_PAIR_APPROVAL':raise PermissionError('awaiting user approval for L pair')
    drawing=bool(re.fullmatch(r'f2-[0-9a-f]{16}-a[01]',trial))
    if not drawing and not re.fullmatch(r'l-[0-9a-f]{16}-l[01]',trial):raise ValueError('invalid trial ID')
    if not 0 < end-time.time() <= 1205:raise ValueError('deadline outside trial budget')
    codex=shutil.which('codex')
    if not codex:raise FileNotFoundError('codex executable not found on PATH')
    local=Path(local).resolve();local.mkdir(exist_ok=False);(local/'minimal').mkdir()
    shutil.copyfile(Path(__file__).with_name('action-schema.json'),local/'schema.json')
    root=Path(os.environ['GEOTREE_SHARED_RUN_ROOT']).resolve()/('f2' if drawing else 'l')/trial/'mailbox'
    def publish(path,obj):
        tmp=path.with_suffix('.tmp')
        write(tmp,obj)
        tmp.replace(path)
    try:
        for i in range(4):
            while time.time()<end:
                if (root/'terminal.json').is_file():
                    write(local/'terminal.json',{'status':'agent_terminal'})
                    return
                request=root/f'observation-{i}.json'
                if request.is_file():
                    raw=request.read_bytes()
                    break
                time.sleep(.4)
            else:raise TimeoutError('trial_deadline')
            envelope=json.loads(raw);obs=envelope['observation'];deadline=min(end,envelope['deadline'])
            (local/f'observation-{i}.json').write_bytes(raw)
            if drawing and i==0:shutil.copyfile(root/'drawing.png',local/'drawing.png')
            sources='the public instruction, attached drawing and Observation' if drawing else 'the public instruction and Observation'
            prompt=(f'You are an independent CAD decision process. Only use {sources}. '
              'Do not call built-in tools or access local files/network/SSH. Return JSON matching the schema and exact request_id. '
              'On turn 0 check_workspace. Later solve with run_freecad, use real feedback to correct errors, or finish done. '
              'Do not repeat a successful check_workspace. code is empty unless run_freecad. Obey script_policy. '
              'No hidden scorer feedback. Give a short public rationale. Observation: '+json.dumps(obs))
            (local/f'request-{i}.txt').write_text(prompt,encoding='utf-8')
            response=local/f'response-{i}.json';events=local/f'events-{i}.jsonl'
            argv=[codex,'exec','--ignore-user-config','--ignore-rules','--ephemeral','--skip-git-repo-check','-s','read-only','-C',str(local/'minimal'),'-m','gpt-6.1-sol']
            for flag in ('shell_tool','unified_exec','multi_agent','skill_search','apps','plugins','remote_plugin','in_app_browser','shell_snapshot'):argv+=['--disable',flag]
            argv+=['--enable','skip_host_skill_discovery','-c','project_doc_max_bytes=0','-c','web_search="disabled"','-c','model_reasoning_effort="high"','--output-schema',str(local/'schema.json')]
            if drawing:argv+=['-i',str(local/'drawing.png')]
            argv+=['--json','-o',str(response),prompt]
            rc=launch(local/f'launch-{i}.json',argv,events,local/f'stderr-{i}.txt',deadline)
            write(local/f'exit-{i}.json',{'returncode':rc,'time':time.time()})
            if rc or time.time()>=deadline:raise RuntimeError(f'model exit={rc} or deadline expired')
            ev=[json.loads(x) for x in events.read_text(encoding='utf-8-sig').splitlines()]
            if any(e.get('item',{}).get('type') not in ('agent_message','reasoning','error') for e in ev if e.get('item')):raise RuntimeError('unexpected model tool event')
            usage=[e['usage'] for e in ev if e.get('type')=='turn.completed'][-1]
            write(local/f'usage-{i}.json',usage)
            a=json.loads(response.read_text(encoding='utf-8-sig'))
            if a.get('request_id')!=obs['request_id']:raise ValueError('stale request id')
            reply=local/f'action-{i}.json';write(reply,dict(action=a,usage=usage))
            if time.time()>=deadline or (root/'terminal.json').exists():raise TimeoutError('late response')
            publish(root/f'action-{i}.json',dict(action=a,usage=usage))
        write(local/'terminal.json',{'status':'decision_limit'})
    except Exception as e:
        write(local/'relay-error.json',{'error':type(e).__name__,'detail':str(e)})
        if root.is_dir():publish(root/'relay-error.json',{'error':type(e).__name__})
        raise


if __name__=='__main__':
    if sys.argv[1]=='supervise':sys.exit(supervise(json.loads(Path(sys.argv[2]).read_text())))
    relay(sys.argv[1],sys.argv[2],float(sys.argv[3]))
