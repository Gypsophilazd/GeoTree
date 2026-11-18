"""Offline task-grounded OCC measurements. No scorer or model integration."""
from dataclasses import dataclass, asdict
from math import isfinite, degrees, atan2
from typing import Protocol

@dataclass(frozen=True)
class ConstraintSpec:
    constraint_id: str
    constraint_type: str
    expected_value: float | None
    unit: str
    coordinate_frame: str
    source_reference: dict
    source_kind: str
    confidence: str
    mapping_status: str
    tolerance: float | None

@dataclass(frozen=True)
class GeometryQuery:
    kind: str
    params: dict

@dataclass(frozen=True)
class RepairProposal:
    artifact_sha256: str
    constraint_id: str
    feature_identity: str
    parameter: str
    proposed_value: float
    unit: str

class ConstraintCandidateProvider(Protocol):
    async def propose_constraints(self, public_instruction: str, drawing: bytes) -> list[ConstraintSpec]: ...

def xyz(v):
    return (float(v.x),float(v.y),float(v.z))

def holes(shape, axis, anchors, window):
    groups=[]
    for f in shape.Faces:
        s=f.Surface
        if type(s).__name__!='Cylinder':continue
        a=xyz(s.Axis)
        if abs(a[axis]) < .999999:continue
        uv=f.ParameterRange
        u,v=(uv[0]+uv[1])/2,(uv[2]+uv[3])/2
        if uv[1]-uv[0]<1e-5:continue
        p=f.valueAt(u,v)
        radial=(p-s.Center)-s.Axis*((p-s.Center).dot(s.Axis))
        if radial.dot(f.normalAt(u,v))>=-1e-6:continue
        point=tuple(x for i,x in enumerate(xyz(s.Center)) if i!=axis)
        if any(abs(x-y)>window for x,y in zip(point,anchors)):continue
        same=next((g for g in groups if max(abs(x-y) for x,y in zip(g['center'],point))<1e-5),None)
        if same is None:
            same={'center':point,'faces':[]};groups.append(same)
        bb=f.BoundBox
        same['faces'].append(dict(radius=float(s.Radius),u_span=float(uv[1]-uv[0]),interval=[getattr(bb,'XYZ'[axis]+e) for e in ('Min','Max')]))
    return groups

def measure(shape,q):
    import FreeCAD as App
    import Part
    p=q.params;b=shape.BoundBox
    if q.kind=='bbox':return getattr(b,p['axis']+'Length'),{'axis':p['axis']},''
    if q.kind in {'bore_diameter','bore_position','bore_centerline','bore_wall_span'}:
        axis=p['axis']; anchors=p['anchor']
        groups=holes(shape,axis,anchors,p['window'])
        evidence={'axis':'XYZ'[axis],'roi_center':anchors,'candidates':groups}
        if len(groups)!=1:return None,evidence,'missing_or_ambiguous_bore_identity'
        g=groups[0];r=g['faces']
        if not any(f['u_span']>=6.28 for f in r):
            return None,evidence,'no_full_cylindrical_wall_witness'
        if max(f['radius'] for f in r)-min(f['radius'] for f in r)>1e-5:
            return None,evidence,'multiple_coaxial_radii'
        if q.kind=='bore_diameter':return 2*r[0]['radius'],evidence,''
        if q.kind=='bore_position':return g['center'][p['index']]-p.get('origin',0),evidence,''
        if q.kind=='bore_wall_span':
            if len(r)!=1:return None,evidence,'wall_split_or_multiple_spans'
            return r[0]['interval'][1]-r[0]['interval'][0],evidence,''
        a=list(g['center']);z=list(g['center'])
        a.insert(axis,getattr(b,'XYZ'[axis]+'Min')-1);z.insert(axis,getattr(b,'XYZ'[axis]+'Max')+1)
        n=shape.common(Part.makeLine(App.Vector(*a),App.Vector(*z))).Length
        return float(n),evidence,'centerline_only_not_full_bore_clearance'
    if q.kind=='end_slope':
        candidates=[]
        for f in shape.Faces:
            if type(f.Surface).__name__!='Plane':continue
            bb=f.BoundBox;n=f.normalAt(0,0)
            if abs(n.y)>1e-6 or not (.02<abs(n.z)<.999):continue
            if abs(bb.XMax-b.XMax)>.001 or abs(bb.ZMin-b.ZMin)>.001 or bb.XMin<b.XMax-p['end_region'] or bb.YLength<p['min_width']:continue
            candidates.append(dict(normal=xyz(n),bbox=[bb.XMin,bb.XMax,bb.ZMin,bb.ZMax],width=bb.YLength,angle=180-degrees(atan2(abs(n.x),abs(n.z)))))
        e={'candidates':candidates,'selector':'end_lower_spanning_plane'}
        if len(candidates)!=1:return None,e,'missing_or_ambiguous_slope'
        return candidates[0]['angle'],e,''
    raise NotImplementedError(q.kind)

def verify(shape,s,q):
    row=asdict(s)|{'measured':None,'status':'UNKNOWN','repair_target':None,'candidate_mapping':{}}
    if s.source_kind not in {'EXPLICIT','DERIVED'} or s.confidence!='reviewed' or s.mapping_status!='verified' or s.expected_value is None or s.tolerance is None:
        return row|{'reason':'insufficient_source_or_coordinate_mapping'}
    if not all(isfinite(x) for x in (s.expected_value,s.tolerance)) or s.tolerance<0:
        return row|{'reason':'invalid_numeric_spec'}
    if not shape.isValid() or len(shape.Solids)!=1:
        return row|{'reason':'missing_valid_unique_solid'}
    if q is None:return row|{'status':'NOT_CHECKABLE','reason':'no_supported_measurement'}
    try:v,e,reason=measure(shape,q)
    except NotImplementedError:return row|{'status':'NOT_CHECKABLE','reason':'no_supported_measurement'}
    except Exception as err:return row|{'reason':'measurement_error:'+type(err).__name__}
    row.update(candidate_mapping=e,reason=reason)
    if v is None or not isfinite(v):return row
    row.update(measured=v,status='PASS' if abs(v-s.expected_value)<=s.tolerance else 'FAIL')
    return row
