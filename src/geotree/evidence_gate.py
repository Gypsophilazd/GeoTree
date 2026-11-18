"""Deterministic text replay + geometry gate. No reward, verifier or model trust."""
from dataclasses import dataclass,asdict
from .constraint_candidates import ConstraintCandidate,extract_text,digest

@dataclass(frozen=True)
class GeometryQuery:
    kind:str
    mapping:dict

@dataclass(frozen=True)
class EvidenceDecision:
    status:str
    reason:str
    query:GeometryQuery|None=None

SUPPORTED={'body_count','solid_count','bbox','feature_present','pad_length','round_body_diameter','round_body_thickness'}

def admit(c,instruction):
    if c.evidence_type!='PUBLIC_TEXT':return EvidenceDecision('CANDIDATE','image hypothesis requires independent evidence')
    fresh=extract_text(instruction)
    if c not in fresh:return EvidenceDecision('AMBIGUOUS','public span/value/mapping failed independent replay')
    same=[x for x in fresh if x.constraint_id==c.constraint_id]
    if len({(x.expected_value,x.unit,x.constraint_type) for x in same})>1:return EvidenceDecision('AMBIGUOUS','conflicting public values')
    if c.constraint_type not in SUPPORTED:return EvidenceDecision('UNSUPPORTED','value extracted; no reliable geometry mapping')
    # Admission authorizes the source and query only. Geometry mapping must still succeed.
    return EvidenceDecision('VERIFIED','deterministically replayed from public text',GeometryQuery(c.constraint_type,c.proposed_feature_mapping))

def _pad(doc,name):
    bodies=[o for o in doc.Objects if o.TypeId=='PartDesign::Body']
    if len(bodies)!=1:return None
    b=bodies[0];f=doc.getObject(name)
    if not f or f.TypeId!='PartDesign::Pad' or b.Tip!=f:return None
    p=f.Profile[0] if isinstance(f.Profile,(tuple,list)) else f.Profile
    if not p or p.TypeId!='Sketcher::SketchObject' or getattr(f,'BaseFeature',None):return None
    features=[o for o in b.Group if o.TypeId.startswith('PartDesign::')]
    if features!=[f]:return None
    return b,f,p

def _round(shape):
    # Exclude internal bores and non-enveloping bosses, independent of target value.
    import FreeCAD as A
    import math
    walls=[]
    for f in shape.Faces:
        s=f.Surface
        if type(s).__name__!='Cylinder':continue
        u0,u1,v0,v1=f.ParameterRange
        if u1-u0<2*math.pi-1e-5:continue
        u,v=(u0+u1)/2,(v0+v1)/2
        delta=f.valueAt(u,v)-s.Center
        rad=delta-s.Axis*delta.dot(s.Axis)
        if rad.dot(f.normalAt(u,v))<=1e-6:continue
        r=A.Rotation(A.Vector(0,0,1),s.Axis).inverted()
        t=shape.copy();t.transformShape(r.toMatrix())
        b=t.BoundBox;d=2*float(s.Radius);ctr=r.multVec(s.Center)
        if max(abs(b.XLength-d),abs(b.YLength-d),abs((b.XMax+b.XMin)/2-ctr.x),abs((b.YMax+b.YMin)/2-ctr.y))>.001:continue
        walls.append((d,b.ZLength,tuple(s.Axis)))
    return walls[0] if len(walls)==1 else None

def verify_document(doc,instruction,candidates,artifact_sha256):
    from .geometry_observer import observe_document
    from .task_geometry import measure,GeometryQuery as OCCQuery
    report=[]
    bodies=[o for o in doc.Objects if o.TypeId=='PartDesign::Body'] if doc is not None else []
    shape=bodies[0].Shape if len(bodies)==1 else None
    valid=shape is not None and not shape.isNull() and shape.isValid() and len(shape.Solids)==1
    generic=observe_document(doc).to_dict() if valid else None
    for c in candidates:
        e=admit(c,instruction);q=e.query
        row=dict(candidate=asdict(c),evidence=e.status,status='UNKNOWN',reason=e.reason,measured=None,artifact_sha256=artifact_sha256,
                 public_sha256=digest(instruction),hard_fail=False)
        if e.status=='UNSUPPORTED':row['status']='NOT_CHECKABLE'
        if q and doc is None:row['reason']='missing_artifact'
        if q and doc is not None:
            v=None
            try:
                if q.kind=='body_count':v=len(bodies)
                elif not valid:row['reason']='invalid_or_ambiguous_single_body'
                elif q.kind=='solid_count':v=generic['solid_count']
                elif q.kind=='bbox':v,_,_=measure(shape,OCCQuery('bbox',q.mapping))
                elif q.kind=='feature_present':v=sum(o.TypeId==q.mapping['type_id'] for o in bodies[0].Group)
                elif q.kind.startswith('round_body'):
                    match=_round(shape)
                    if match:
                        v=match[q.kind=='round_body_thickness'];row['geometry_axis']=match[2]
                    else:row['reason']='no_unique_external_cylindrical_envelope'
                elif q.kind=='pad_length':
                    hit=_pad(doc,q.mapping['feature'])
                    if hit:
                        b,f,p=hit
                        if not f.Reversed and f.Type=='Length' and p.Placement.Rotation.Angle<1e-6 and b.Placement.Rotation.Angle<1e-6 and abs(shape.BoundBox.ZLength-f.Length.Value)<.001:
                            v=shape.BoundBox.ZLength
                    if v is None:row['reason']='pad_identity_or_geometric_span_unconfirmed'
            except (RuntimeError,ValueError,AttributeError,TypeError) as err:row['reason']='measurement_error:'+type(err).__name__
            if v is not None:
                tol=0 if c.unit=='count' else .01
                row.update(measured=float(v),tolerance=tol,status='PASS' if abs(v-c.expected_value)<=tol else 'FAIL',
                    reason='public_text_replay_and_unique_measurement')
                row['hard_fail']=row['status']=='FAIL'
        report.append(row)
    return dict(artifact_status='MISSING' if doc is None else 'VALID' if valid else 'INVALID_OR_AMBIGUOUS',
      artifact_sha256=artifact_sha256,results=report)
