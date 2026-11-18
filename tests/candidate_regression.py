import asyncio,json,tempfile
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from geotree.constraint_candidates import ConstraintCandidate,extract_text,propose_drawing
from geotree.evidence_gate import admit
from geotree.nosearch import NoSearchRuntime,MockProvider,FeedbackRecorder,ModelReply
from geotree.verification_harness import VerificationExecutor,PublicConstraintProvider
D=Path(__file__).parent

ins='Overall X extent = 34 mm\nSet Pad.Length to 12 mm.\nRequire one PartDesign::Pad.'
def unit():
    cs=extract_text(ins)
    assert len(cs)==3 and all(admit(c,ins).status=='VERIFIED' for c in cs)
    assert admit(replace(cs[0],expected_value=35),ins).status=='AMBIGUOUS'
    bad=ins+'\nOverall X extent = 35 mm'
    assert admit(extract_text(bad)[0],bad).status=='AMBIGUOUS'
    hole=extract_text('Bore center at X = 1 mm, Y = 2 mm in the XY plane.')[0]
    assert hole.proposed_feature_mapping=={'xy':[1.,2.]}
    assert admit(hole,'Bore center at X = 1 mm, Y = 2 mm in the XY plane.').status=='UNSUPPORTED'
    assert not extract_text('approximate diameter of arbitrary component')
    print('PASS replay, tamper, conflicts, explicit edit/presence, hole map abstention')
class VLM:
    def __init__(self,fields):self.fields=fields
    async def propose(self,o):return ModelReply({'candidates':[self.fields]}, {})
async def image_tests():
    x=dict(constraint_id='x',constraint_type='bbox',expected_value=12,unit='mm',image_roi=[1,2,5,6],coordinate_frame='draft',uncertainty='unknown')
    c,_=await propose_drawing(VLM(x),'public','a'*64,(20,20));assert admit(c[0],'public').status=='CANDIDATE'
    for bad in (x|{'reviewed':True},x|{'verified':True},x|{'image_roi':[0,0,21,20]},x|{'expected_value':float('nan')}):
        try:await propose_drawing(VLM(bad),'public','a'*64,(20,20))
        except ValueError:pass
        else:raise AssertionError('invalid authority/schema accepted')
    print('PASS image ROI, finite numeric output, no self-certification')

if __name__=="__main__":
    unit();asyncio.run(image_tests())
