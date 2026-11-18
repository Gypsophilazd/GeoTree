"""Opt-in one-operation repair adapter. Call only in a restricted FreeCAD worker."""
from dataclasses import dataclass,asdict
import hashlib,os,tempfile,time
from pathlib import Path
from .constraint_candidates import extract_text,digest
from .evidence_gate import verify_document,_pad

@dataclass(frozen=True)
class RepairRequest:
    artifact_sha256:str
    public_sha256:str
    constraint_id:str
    operation:str
    target_feature:str

def _sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def attempt_pad_length(source, workdir, instruction, req):
    """Source/workdir are selected by trusted runner, never supplied by a model."""
    import FreeCAD as App,Part
    from shutil import copyfile
    start=time.monotonic();trace=['PROPOSED']
    source=Path(source);workdir=Path(workdir).resolve()
    def done(st,reason,**kwargs):
        return dict(request=asdict(req),status=st,reason=reason,trace=trace+[st],seconds=time.monotonic()-start,**kwargs)
    if source.is_symlink() or source.suffix!='.FCStd' or not source.is_file() or source.stat().st_size>20_000_000:
        return done('REJECTED','invalid_source')
    if _sha(source)!=req.artifact_sha256 or digest(instruction)!=req.public_sha256:
        return done('REJECTED','hash_mismatch')
    if req.operation!='SET_ISOLATED_PAD_LENGTH':
        return done('REJECTED','operation_not_supported')
    cs=extract_text(instruction)
    rows=[c for c in cs if c.constraint_id==req.constraint_id and c.constraint_type=='pad_length']
    if len(rows)!=1 or rows[0].proposed_feature_mapping.get('feature')!=req.target_feature:
        return done('UNKNOWN','no_unique_public_feature_parameter')
    c=rows[0];dest=workdir/'verified.FCStd'
    if not workdir.is_dir() or dest.exists() or dest.is_symlink():return done('REJECTED','output_not_empty')
    with tempfile.TemporaryDirectory(dir=workdir,prefix='stage-') as tmp:
        tmp=Path(tmp);copy=tmp/'input.FCStd';copyfile(source,copy)
        if _sha(copy)!=req.artifact_sha256:return done('REJECTED','copy_hash_mismatch')
        doc=None
        try:
            doc=App.openDocument(str(copy))
            pre=verify_document(doc,instruction,cs,req.artifact_sha256)
            row=next(x for x in pre['results'] if x['candidate']['constraint_id']==c.constraint_id)
            if row['status']=='PASS':return done('REJECTED','already_conforming')
            if not row['hard_fail']:return done('UNKNOWN','no_trusted_fail')
            hit=_pad(doc,req.target_feature)
            if not hit:return done('REJECTED','non_isolated_pad')
            b,f,p=hit
            # Deliberately narrow: one body, one sketch/one pad, no other consumers or attachments.
            if set(x.Name for x in b.Group if x.TypeId.startswith(('Sketcher::','PartDesign::')))!={f.Name,p.Name} or any(x.Name not in {b.Name,f.Name,p.Name} for x in f.InList+p.InList):
                return done('REJECTED','dependency_not_isolated')
            if any(o.TypeId not in {'PartDesign::Body','PartDesign::Pad','Sketcher::SketchObject','App::Origin','App::Line','App::Plane','App::Point'} for o in doc.Objects):
                return done('REJECTED','unexpected_document_type')
            if any(getattr(x,'ExpressionEngine',[]) for x in doc.Objects) or p.MapMode!='Deactivated' or getattr(p,'Support',None) or getattr(p,'AttachmentSupport',None):
                return done('REJECTED','attachment_or_expression')
            if b.Placement.Base.Length>1e-6 or p.Placement.Base.z!=0 or f.Reversed or f.Type!='Length' or f.Midplane or abs(f.TaperAngle.Value)>1e-6 or len(p.Shape.Wires)!=1 or not .1<c.expected_value<1000:
                return done('REJECTED','nonstandard_pad')
            before=b.Shape.copy();old=float(f.Length.Value)
            base=Part.Face(p.Shape.Wires[0]);v=App.Vector
            prism=base.extrude(v(0,0,old))
            if before.cut(prism).Volume>1e-5 or prism.cut(before).Volume>1e-5:
                return done('REJECTED','old_shape_not_exact_prism')
            trace.append('VALIDATED')
            f.Length=c.expected_value;trace.append('EXECUTED');doc.recompute()
            if any(set(o.State)&{'Invalid','Error','Touched'} for o in doc.Objects):
                return done('REJECTED','recompute_fault')
            changed=tmp/'edited.FCStd';doc.saveAs(str(changed));App.closeDocument(doc.Name);doc=None
            doc=App.openDocument(str(changed));h=_sha(changed)
            post=verify_document(doc,instruction,cs,h)
            recheck={x['candidate']['constraint_id']:x for x in post['results']}
            reg=all(recheck[x['candidate']['constraint_id']]['status']=='PASS' for x in pre['results'] if x['status']=='PASS')
            b2,f2,p2=_pad(doc,req.target_feature)
            after=b2.Shape
            envelope=base.extrude(v(0,0,max(old,c.expected_value)))
            outside=[before.cut(after).cut(envelope).Volume,after.cut(before).cut(envelope).Volume]
            target=base.extrude(v(0,0,c.expected_value))
            exact=[after.cut(target).Volume,target.cut(after).Volume]
            if not reg or post['artifact_status']!='VALID' or recheck[c.constraint_id]['status']!='PASS' or max(outside+exact)>1e-5:
                return done('REJECTED','postcondition_failed',outside_mm3=outside,exact_prism_diff_mm3=exact)
            App.closeDocument(doc.Name);doc=None
            if _sha(source)!=req.artifact_sha256:return done('REJECTED','source_changed')
            # Exclusive link publish; never overwrite existing deliverables.
            os.link(changed,dest)
            return done('VERIFIED','saved_reopened_verified',output_sha256=h,
              property_changes={req.target_feature+'.Length':[old,c.expected_value]},outside_mm3=outside,exact_prism_diff_mm3=exact,post=post)
        except (AttributeError,ValueError,RuntimeError,TypeError,OSError) as err:
            return done('REJECTED','worker_error:'+type(err).__name__)
        finally:
            if doc is not None:App.closeDocument(doc.Name)
