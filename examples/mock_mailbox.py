"""Known synthetic actions, not a model or benchmark result."""
import json
import sys
import time
from pathlib import Path

from geotree.paired_agent import atomic

mailbox = Path(sys.argv[1])
deadline = time.monotonic() + 85
code = """
import FreeCAD as App
import Part
import Sketcher
d = App.newDocument()
b = d.addObject('PartDesign::Body', 'Body')
s = b.newObject('Sketcher::SketchObject', 'Profile')
s.addGeometry(Part.Circle(App.Vector(0,0,0), App.Vector(0,0,1), 5), False)
p = b.newObject('PartDesign::Pad', 'Pad')
p.Profile = s
p.Length = 12
d.recompute()
d.saveAs('/app/answer.FCStd')
"""
for turn, action in enumerate(('check_workspace', 'run_freecad', 'done')):
    request = mailbox / f'observation-{turn}.json'
    while not request.exists():
        if time.monotonic() >= deadline or (mailbox / 'terminal.json').exists():
            raise RuntimeError(f'No request: {request}')
        time.sleep(.1)
    obs = json.loads(request.read_text())['observation']
    if turn == 2:
        feedback = obs['history'][-1]
        assert feedback['exit_status'] == 0, feedback
        checks = feedback['task_grounded']['counts']
        assert checks['PASS'] == 1 and checks['FAIL'] == 0, feedback
    atomic(mailbox / f'action-{turn}.json', dict(
        action=dict(request_id=obs['request_id'], action=action, code=code if turn == 1 else '',
                    reason='synthetic smoke fixture'), usage=dict(input_tokens=0,output_tokens=0)))
print('PASS synthetic Harbor mailbox, post-CAD evidence feedback; real model calls=0')
