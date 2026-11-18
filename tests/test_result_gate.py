import json,tempfile,unittest
from pathlib import Path
from scripts.result_gate import gate
class Gate(unittest.TestCase):
 def setUp(self):
    self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
    self.r=Path(self.tmp.name)/'trial';p=self.r/'jobs/trial/only'
    (p/'agent').mkdir(parents=True);(self.r/'exit').write_text('0')
    self.result=p/'result.json';self.trace=p/'agent/trace.jsonl'
    self.write();self.trace.write_text('{"event":"terminal","data":{"status":"done"}}\n')
 def write(self,**changes):
    self.result.write_text(json.dumps(dict(exception_info=None,finished_at='now',verifier_environment_mode='separate',verifier_result={'rewards':{'reward':0.0}})|changes))
 def test_zero_is_reward(self):self.assertEqual(gate(self.r,True),'done')
 def test_missing_trace(self):
    self.trace.unlink()
    with self.assertRaises(FileNotFoundError):gate(self.r)
 def test_worker_error(self):
    with self.trace.open('a') as f:f.write('{"event":"feedback","data":{"task_grounded":{"status":"ERROR"}}}\n')
    with self.assertRaisesRegex(ValueError,'infrastructure'):gate(self.r)
 def test_missing_score(self):
    self.write(verifier_result=None)
    self.assertEqual(gate(self.r),'done')
    with self.assertRaisesRegex(ValueError,'reward'):gate(self.r,True)
 def test_trial_exception(self):
    self.write(exception_info={'exception_type':'TypeError'})
    with self.assertRaisesRegex(ValueError,'TypeError'):gate(self.r)
if __name__=='__main__':unittest.main()
