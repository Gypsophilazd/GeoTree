import unittest,tempfile,json
from types import SimpleNamespace
from geotree.geometry_reader import FixedGeometryReader,COMMAND
from geotree.geometry_observer import GeometryObservation
class Env:
 def __init__(self,rc=0):self.rc=rc;self.calls=[]
 async def exec(self,command,**kw):
  self.calls.append((command,kw));o=GeometryObservation();o.metadata['artifact_sha256']='a'*64
  return SimpleNamespace(return_code=self.rc,stdout='GEOTREE_OBSERVATION='+json.dumps(o.to_dict()),stderr=None)
class ReaderTests(unittest.IsolatedAsyncioTestCase):
 async def test_fixed_binding(self):
  with tempfile.TemporaryDirectory() as d:
   e=Env();r=FixedGeometryReader(e,d);r.action_id='action-1';o=await r()
   self.assertEqual(e.calls[0][0],COMMAND);self.assertEqual(e.calls[0][1]['user'],'65534');self.assertEqual(o.metadata['action_id'],'action-1');self.assertEqual(o.constraint_checks,[])
 async def test_failure(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(RuntimeError):await FixedGeometryReader(Env(1),d)()
if __name__=='__main__':unittest.main()
