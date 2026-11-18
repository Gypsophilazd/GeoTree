"""Fixed read-only operation, shared across both arms; no candidate code execution."""
import json,stat
from pathlib import Path
from .constraint_candidates import extract_text,digest
from .evidence_gate import verify_document
from .verification_harness import disposition

def verify_file(path,instruction):
    import FreeCAD as App
    cs=extract_text(instruction)
    try:info=path.lstat()
    except FileNotFoundError:return verify_document(None,instruction,cs,None)
    if not stat.S_ISREG(info.st_mode) or not 0<info.st_size<=20_000_000:
        return dict(artifact_status='REJECTED_ARTIFACT',artifact_sha256=None,results=[])
    h=digest(path.read_bytes())
    try:doc=App.openDocument(str(path))
    except (RuntimeError,ValueError,OSError):return dict(artifact_status='UNREADABLE',artifact_sha256=h,results=[])
    try:r=verify_document(doc,instruction,cs,h)
    finally:App.closeDocument(doc.Name)
    if h!=digest(path.read_bytes()):raise ValueError('artifact_changed')
    return r

def repair_policy(report):
    failed=[x for x in report['results'] if x['hard_fail']]
    if not failed:return {'status':'NOT_RUN','reason':'no_credible_fail'}
    supported=[x for x in failed if x['candidate']['constraint_type']=='pad_length']
    if not supported:return {'status':'UNKNOWN','reason':'no_supported_safe_repair_mapping'}
    # The public task contract reruns answer.py. FCStd-only replacement would
    # be discarded. No sanctioned source-transform operation is available.
    return {'status':'REJECTED','reason':'submission_requires_replayable_answer_py'}

def main():
    i=Path('/opt/geotree-k/instruction.md').read_text(encoding='utf-8')
    r=verify_file(Path('/app/answer.FCStd'),i)
    print('GEOTREE_K='+json.dumps(dict(public_sha256=digest(i),report=r,disposition=disposition(r),repair=repair_policy(r)),allow_nan=False))
