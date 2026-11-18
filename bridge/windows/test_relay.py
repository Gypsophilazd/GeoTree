import ctypes as c,sys,subprocess as s,tempfile,time
from pathlib import Path
from relay import launch
with tempfile.TemporaryDirectory() as d:
 p=Path(d);o=p/'out';e=p/'err';spec=p/'spec.json'
 def run(code,t=10):return launch(spec,[sys.executable,'-c',code],o,e,time.time()+t)
 assert run("print('normal')")==0 and o.read_text().strip()=='normal'
 assert run("raise SystemExit(7)")==7
 assert run("import subprocess,sys,time; q=subprocess.Popen([sys.executable,'-c','import time;time.sleep(50)']);print(q.pid,flush=True);time.sleep(50)",2)==124
 pid=int(o.read_text());k=c.windll.kernel32
 k.OpenProcess.restype=c.c_void_p
 h=k.OpenProcess(0x100000,False,pid)
 if h:
  assert k.WaitForSingleObject(c.c_void_p(h),3000)==0
  k.CloseHandle(c.c_void_p(h))
 print('PASS normal=0 abnormal=7 timeout=124 descendant exited; parent alive')
