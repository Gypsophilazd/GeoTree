import importlib,os,tempfile,unittest
from fastapi.testclient import TestClient
from pathlib import Path

class API(unittest.TestCase):
 def test_persistence_quota_and_cancellation(self):
  with tempfile.TemporaryDirectory() as d:
   from studio.backend import app as mod
   orig=mod.DATA
   try:
    mod.DATA=Path(d)
    t=TestClient(mod.app)
    r=t.post('/api/jobs',json={'prompt':'fixture only','provider':'Codex'},headers={'origin':'https://untrusted.invalid'})
    self.assertEqual(r.status_code,403)
    for _ in range(2):
     j=t.post('/api/jobs',json={'prompt':'fixture only','provider':'Codex'}).json()
     self.assertEqual(j['status'],'queued')
     c=t.post('/api/jobs/'+j['id']+'/cancel',json={});self.assertEqual(c.json()['status'],'cancelled')
     self.assertEqual(t.get('/api/jobs/'+j['id']).json()['events'][-1]['event'],'cancellation_requested')
     self.assertEqual(t.post('/bridge/claim',json={}).json(),{})
    self.assertEqual(t.post('/api/jobs',json={'prompt':'third','provider':'Codex'}).status_code,409)
   finally:mod.DATA=orig
if __name__=='__main__':unittest.main(verbosity=2)
