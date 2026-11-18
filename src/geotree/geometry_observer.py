"""Read-only, deterministic inspection of agent-visible CAD state.
No scorer, target mesh, LLM, script execution, save, or document recompute.
Units: mm, mm^3. Validity is not task correctness.
"""
from dataclasses import dataclass,field,asdict
import hashlib,json,math,time
from pathlib import Path

@dataclass
class GeometryObservation:
    shape_valid: bool | None = None
    solid_count: int | None = None
    volume: float | None = None
    bounding_box: dict | None = None
    body_count: int | None = None
    feature_types: list = field(default_factory=list)
    features: list = field(default_factory=list)
    dependency_warnings: list = field(default_factory=list)
    constraint_checks: list = field(default_factory=list)
    execution_errors: list = field(default_factory=list)
    geometry_errors: list = field(default_factory=list)
    unknown_fields: list = field(default_factory=lambda:['target_geometry_correctness','target_volume','unmapped_dimensions'])
    metadata: dict = field(default_factory=dict)
    def to_dict(self): return asdict(self)

def check_constraints(obs,constraints):
    """Caller supplies independently reviewed public evidence, not model confidence."""
    out=[]
    for c in constraints:
        row={'id':c.get('id'),'status':'UNKNOWN','metric':c.get('metric'),'expected':c.get('expected'),'source':c.get('source')}
        src=c.get('source',{})
        if src.get('kind') not in {'task_text','drawing_annotation','fixture'} or src.get('reviewed') is not True or not src.get('locator'):
            row['reason']='unreviewed_or_missing_public_evidence';out.append(row);continue
        metric=c.get('metric');actual=obs.get(metric)
        if metric and metric.startswith('bounding_box.'):
            actual=(obs.get('bounding_box') or {}).get(metric.split('.',1)[1])
        row['actual']=actual
        expected=c.get('expected')
        if actual is None or expected is None or c.get('mapping_reviewed') is not True:
            row['reason']='unknown_measurement_target_or_mapping';out.append(row);continue
        if not isinstance(actual,(int,float,bool)) or not isinstance(expected,(int,float,bool)):
            row['reason']='unsupported_metric';out.append(row);continue
        tol=c.get('tolerance',0)
        if not isinstance(tol,(int,float)) or not math.isfinite(tol) or tol<0 or not all(math.isfinite(float(x)) for x in [actual,expected]):
            row['reason']='invalid_numeric_specification';out.append(row);continue
        op=c.get('op','eq')
        if op=='eq':ok=abs(actual-expected)<=tol
        elif op=='le':ok=actual<=expected+tol
        elif op=='ge':ok=actual>=expected-tol
        else:row['reason']='unsupported_comparison';out.append(row);continue
        row.update(status='PASS' if ok else 'FAIL',tolerance=tol,op=op)
        out.append(row)
    return out

def _refs(value):
    if hasattr(value,'Name'):return [value.Name]
    if isinstance(value,(list,tuple)):return [n for x in value for n in _refs(x)]
    return []

def observe_document(doc,constraints=(),execution_errors=()):
    start=time.monotonic();o=GeometryObservation(execution_errors=list(execution_errors));objects=list(doc.Objects);names={x.Name for x in objects}
    bodies=[x for x in objects if x.TypeId=='PartDesign::Body'];o.body_count=len(bodies)
    if len(bodies)==1:target=bodies[0]
    elif not bodies:
        shaped=[x for x in objects if hasattr(x,'Shape') and not x.TypeId.startswith('Sketcher::')]
        target=shaped[0] if len(shaped)==1 else None
    else:target=None
    if target is None:o.unknown_fields.extend(['shape_valid','solid_count','volume','bounding_box']);o.geometry_errors.append('missing_or_ambiguous_result_shape')
    else:
        shape=target.Shape
        if shape.isNull():
            o.shape_valid=False;o.solid_count=0;o.geometry_errors.append('null_shape');o.unknown_fields.extend(['volume','bounding_box'])
        else:
            try:
                o.shape_valid=bool(shape.isValid());o.solid_count=len(shape.Solids);o.volume=float(shape.Volume)
                b=shape.BoundBox;o.bounding_box={k:float(getattr(b,k)) for k in ['XMin','XMax','YMin','YMax','ZMin','ZMax','XLength','YLength','ZLength']}
                if not o.shape_valid:o.geometry_errors.append('invalid_brep')
                if o.solid_count!=1:o.geometry_errors.append('not_single_solid')
            except Exception as e:o.geometry_errors.append(type(e).__name__+': '+str(e));o.unknown_fields.extend(['shape_valid','solid_count','volume','bounding_box'])
    edges={}
    for x in objects:
        if not (x.TypeId.startswith('PartDesign::') or x.TypeId.startswith('Sketcher::')):continue
        info={'name':x.Name,'type':x.TypeId,'state':list(x.State),'dependencies':{}}
        o.feature_types.append(x.TypeId)
        for prop in ['Profile','Sections','BaseFeature']:
            if prop not in x.PropertiesList:continue
            refs=_refs(getattr(x,prop));info['dependencies'][prop]=refs
            for name in refs:
                if name not in names:o.dependency_warnings.append(f'{x.Name}.{prop}: missing {name}')
            edges.setdefault(x.Name,[]).extend(refs)
        if x.TypeId in {'PartDesign::Pad','PartDesign::Pocket','PartDesign::SubtractiveLoft'} and not info['dependencies'].get('Profile'):
            o.dependency_warnings.append(f'{x.Name}: missing Profile')
        if any(s in {'Invalid','Error','Touched'} for s in info['state']):o.dependency_warnings.append(f'{x.Name}: state={info["state"]}; stored geometry may be stale')
        for prop in ['Length','Reversed']:
            if prop in x.PropertiesList:
                v=getattr(x,prop);info[prop]=float(v.Value) if hasattr(v,'Value') else v
        if x.TypeId.startswith('Sketcher::'):
            info['geometry_count']=x.GeometryCount;info['constraint_count']=x.ConstraintCount
            info['fully_constrained']=getattr(x,'FullyConstrained',None)
            if info['fully_constrained'] is False:o.dependency_warnings.append(f'{x.Name}: underconstrained (not necessarily incorrect)')
        if hasattr(x,'Shape') and not x.Shape.isNull() and not x.TypeId.startswith('Sketcher::'):
            info['volume']=float(x.Shape.Volume);info['solid_count']=len(x.Shape.Solids)
        o.features.append(info)
    colors={}
    def visit(n):
        if colors.get(n)==1:return True
        if colors.get(n)==2:return False
        colors[n]=1
        cyclic=any(visit(q) for q in edges.get(n,[]) if q in edges)
        colors[n]=2
        return cyclic
    if any(visit(n) for n in edges):o.dependency_warnings.append('dependency_cycle')
    o.constraint_checks=check_constraints(o.to_dict(),constraints)
    o.metadata={'observer_version':'0.1.0','units':{'length':'mm','volume':'mm^3'},'elapsed_sec':time.monotonic()-start,'recomputed':False,'correctness_claim':False}
    return o

def inspect_file(path,allowed_root,constraints=()):
    p=Path(path);root=Path(allowed_root).resolve()
    if p.is_symlink():raise ValueError('symlink artifact rejected')
    p=p.resolve()
    if not p.is_relative_to(root) or p.suffix!='.FCStd' or not p.is_file():raise ValueError('artifact outside allowed root or unsupported file')
    if p.stat().st_size>20000000:raise ValueError('artifact size budget')
    import FreeCAD as App
    before=hashlib.sha256(p.read_bytes()).hexdigest();doc=App.openDocument(str(p))
    try:o=observe_document(doc,constraints)
    finally:App.closeDocument(doc.Name)
    after=hashlib.sha256(p.read_bytes()).hexdigest()
    if before!=after:raise RuntimeError('input unexpectedly modified')
    o.metadata.update(artifact_sha256=before,freecad_version='.'.join(App.Version()[:3]))
    return o

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('artifact');parser.add_argument('--allowed-root',required=True);parser.add_argument('--constraints');a=parser.parse_args()
    cs=json.loads(Path(a.constraints).read_text()) if a.constraints else []
    print(json.dumps(inspect_file(a.artifact,a.allowed_root,cs).to_dict(),indent=2,allow_nan=False))
