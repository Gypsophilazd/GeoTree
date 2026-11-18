"""Offline E02-I transaction; source binding, typed command and measured gates."""
from dataclasses import dataclass,asdict,field
from pathlib import Path
import hashlib,json,time,math
import FreeCAD as App, Part, Sketcher
from check import compare,intervals,fixture
from geotree.task_geometry import ConstraintSpec,GeometryQuery,verify
V=App.Vector

@dataclass
class RepairProposal:
    artifact_sha256:str
    constraint_id:str
    target_feature_identity:dict
    expected_relation:str
    measured_relation:str|None
    proposed_operation:str='REANCHOR_PLANAR_POCKET'
    parameter_changes:dict=field(default_factory=dict)
    prerequisite_checks:list=field(default_factory=list)
    affected_dependencies:list=field(default_factory=list)
    confidence:str='researcher_signed_task_and_frame'
    uncertainty:list=field(default_factory=lambda:['22 mm preserved, not independently validated as target depth'])
    execution_status:str='PROPOSED'
    events:list=field(default_factory=list)
    def state(self,st,reason):
        self.execution_status=st;self.events.append(dict(state=st,reason=reason,time=time.time()))

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def obj(v):return v[0] if isinstance(v,(list,tuple)) and v else v
def z(o):return float(o.Placement.Base.z)
def val(x):return float(x.Value) if hasattr(x,'Value') else x
def body(doc):
    b,=[x for x in doc.Objects if x.TypeId=='PartDesign::Body'];return b
def placement(o):return [*o.Placement.Base,*o.Placement.Rotation.Q]
def links(doc):
    rows=[]
    for o in doc.Objects:
        for k in o.PropertiesList:
            t=o.getTypeIdOfProperty(k)
            if 'Link' not in t:continue
            v=getattr(o,k)
            if not v:continue
            vs=v if t.endswith('List') else [v]
            for u in vs:
                f=obj(u); subs=u[1] if isinstance(u,(tuple,list)) and len(u)>1 else []
                if isinstance(subs,str):subs=[subs]
                if f is not None:rows.append(dict(source=o.Name,property=k,target=getattr(f,'Name',str(f)),subelements=list(subs or [])))
    return rows
def signature(doc):
    result={}
    for o in doc.Objects:
        p={}
        for k in ('Length','Reversed','Type','TaperAngle','MapMode','AttachmentOffset','Midplane','Refine'):
            if k in o.PropertiesList:
                x=val(getattr(o,k));p[k]=x if isinstance(x,(int,float,str,bool)) else str(x)
        if 'Placement' in o.PropertiesList:p['Placement']=placement(o)
        if o.TypeId=='Sketcher::SketchObject':
            p['Geometry']=[g.toShape().exportBrepToString() for g in o.Geometry]
            p['Constraints']=[str(c) for c in o.Constraints]
        p['Expressions']=[list(e) for e in getattr(o,'ExpressionEngine',[])]
        result[o.Name]=dict(type=o.TypeId,properties=p)
    return dict(objects=result,links=links(doc),tip=body(doc).Tip.Name,group=[x.Name for x in body(doc).Group])
def status(doc):
    return {o.Name:list(o.State) for o in doc.Objects if any(s in ('Invalid','Error','Touched') for s in o.State)}
def unique_owner(b):
    # First Pocket that changes all three previously full local deck probes to the bottom opening.
    out=[]
    for f in b.Group:
        if f.TypeId!='PartDesign::Pocket' or not f.BaseFeature:continue
        before=[intervals(f.BaseFeature.Shape,x,0) for x in (35,45,55)]
        after=[intervals(f.Shape,x,0) for x in (35,45,55)]
        if all(len(a)==1 and abs(a[0][0])<.02 and abs(a[0][1]-28)<.02 for a in before) and all(len(a)==1 and .05<a[0][0]<27.95 and abs(a[0][1]-28)<.02 for a in after):
            out.append(f.Name)
    return out
def gate(doc,actual_sha,p,alignment,measurement):
    def stop(st,why):p.state(st,why);return False
    if actual_sha!=p.artifact_sha256:return stop('REJECTED','artifact_sha_mismatch')
    p.prerequisite_checks.append('input_hash_matches')
    if actual_sha not in alignment['artifact_frame_approvals']:return stop('UNKNOWN','unapproved_frame')
    p.prerequisite_checks.append('signed_frame')
    if measurement['verdict']=='PASS':return stop('REJECTED','already_conforming_no_edit')
    if measurement['verdict']!='FAIL' or measurement['measured_relation']!='BOTTOM' or p.expected_relation!='TOP':
        return stop('UNKNOWN','no_verified_target_fail')
    if p.proposed_operation!='REANCHOR_PLANAR_POCKET':return stop('REJECTED','operation_not_allowed')
    b=body(doc);f=doc.getObject(p.target_feature_identity['feature'])
    if not f or f.TypeId!='PartDesign::Pocket' or obj(f.Profile) is None or obj(f.Profile).Name!=p.target_feature_identity['profile']:
        return stop('UNKNOWN','profile_identity_mismatch')
    s=obj(f.Profile)
    owners=unique_owner(b)
    if owners!=[f.Name]:return stop('UNKNOWN','unique_BRep_owner_not_confirmed')
    p.prerequisite_checks.append('unique_BRep_transition_and_profile')
    group=list(b.Group); touched={o.Name for o in group[group.index(f):]}|{s.Name}
    p.affected_dependencies=[r for r in links(doc) if r['target'] in touched or r['source'] in touched]
    # Stop on subelement-dependent model (conservative whole-doc rule).
    unsafe=[r for r in links(doc) if any(k for k in r['subelements'])]
    if unsafe:
        p.prerequisite_checks.append({'subelement_dependencies':unsafe});return stop('REJECTED','subelement_dependencies_present')
    if any(getattr(o,'ExpressionEngine',[]) for o in doc.Objects):return stop('REJECTED','expressions_present')
    if s.TypeId!='Sketcher::SketchObject' or getattr(s,'MapMode','Deactivated')!='Deactivated' or getattr(s,'AttachmentSupport',None) or getattr(s,'Support',None):
        return stop('REJECTED','profile_not_unattached')
    if abs(z(s))>.001 or s.Placement.Rotation.multVec(V(0,0,1)).sub(V(0,0,1)).Length>1e-6:
        return stop('REJECTED','unexpected_profile_plane')
    if any(abs(x)>1e-6 for x in (z(b), b.Placement.Base.x,b.Placement.Base.y,b.Placement.Rotation.Angle)):
        return stop('REJECTED','unexpected_body_transform')
    if not f.Reversed or f.Type!='Length' or not .05<float(f.Length.Value)<27.95 or abs(float(f.TaperAngle.Value))>1e-6:
        return stop('REJECTED','unexpected_pocket_parameters')
    if len(s.Shape.Wires)!=1:return stop('UNKNOWN','profile_not_single_wire')
    p.prerequisite_checks+=['no_subelement_or_expression_dependencies','unattached_XY_profile','length_pocket_and_reviewed_deck']
    p.parameter_changes={s.Name+'.Placement.Base.z':[0,28],f.Name+'.Reversed':[True,False],f.Name+'.Length':[float(f.Length.Value)]*2}
    p.state('VALIDATED','only typed profile plane and pocket direction can be edited')
    return True
def apply(doc,p):
    assert p.execution_status=='VALIDATED'
    f=doc.getObject(p.target_feature_identity['feature']);s=obj(f.Profile)
    env=Part.Face(s.Shape.Wires[0]).extrude(V(0,0,28))
    pl=s.Placement;pl.Base=V(pl.Base.x,pl.Base.y,28);s.Placement=pl
    f.Reversed=False;p.state('EXECUTED','moved existing sketch plane, flipped existing pocket')
    return env
def compare_side(s,h,al):
    return compare(s,h,al)
def validate16(s,rows):
    return [verify(s,ConstraintSpec(**x['spec']),GeometryQuery(**x['query'])) for x in rows]
def make_proposal(h,b,f,s,m):
    return RepairProposal(h,'main_cavity_open_side',{'body':b,'feature':f,'profile':s},'TOP',m)
def synthetic(al,out):
    cases={}
    for key,side,expect in [('already_top','TOP','REJECTED'),('reverse','BOTTOM','VERIFIED'),('unknown_frame','BOTTOM','UNKNOWN'),('unsafe_link','BOTTOM','REJECTED'),('wrong_hash','BOTTOM','REJECTED')]:
        doc,s=fixture(side)
        try:
            h='fixture-'+key
            approval=al|{'artifact_frame_approvals':{} if key=='unknown_frame' else {h:'synthetic'}}
            if key=='unsafe_link':
                o=doc.addObject('App::FeaturePython','DownstreamProbe')
                o.addProperty('App::PropertyLinkSub','UnsafeRef');o.UnsafeRef=(doc.getObject('Pocket'),['Face1'])
            m=compare_side(s,h,approval);p=make_proposal('wrong' if key=='wrong_hash' else h,'Body','Pocket','Cavity',m['measured_relation'])
            before=signature(doc)
            if gate(doc,h,p,approval,m):
                apply(doc,p);doc.recompute()
                assert not status(doc)
                r=compare_side(body(doc).Shape,h,approval);assert r['verdict']=='PASS'
                p.state('VERIFIED','synthetic orientation corrected')
            else:assert signature(doc)==before
            assert p.execution_status==expect,(key,p)
            cases[key]=asdict(p)
        finally:App.closeDocument(doc.Name)
    out['synthetic']=cases
def process(out):
    path=Path('/inputs/a1.FCStd');h=sha(path)
    expected=Path('/work/source.sha256').read_text().strip()
    assert h==expected
    al=json.loads(Path('/work/alignment.json').read_text())
    g=json.loads(Path('/work/public-specs.json').read_text())['specs']
    rows=[x for x in g if x['query'] is not None];assert len(rows)==16
    copies={};p=None;envelope=None
    for arm in ('C0','C1'):
        start=time.monotonic()
        doc=App.openDocument(str(path))
        try:
            b=body(doc);before=signature(doc)
            if arm=='C1':
                m=compare_side(b.Shape,h,al)
                p=make_proposal(expected,b.Name,'UndersideCavity','UndersideCavityOutline',m['measured_relation'])
                ok=gate(doc,h,p,al,m)
                out['proposal']=asdict(p)
                out['preflight']=dict(signature=before,owner_candidates=unique_owner(b),target_profile_support=str(getattr(doc.getObject('UndersideCavityOutline'),'Support',None)),measurement=m)
                if not ok:return
                envelope=apply(doc,p)
            doc.recompute()
            faults=status(doc)
            out[arm]={'recompute_faults':faults}
            if faults:
                if p:p.state('REJECTED','recompute_faults');out['proposal']=asdict(p)
                return
            f=Path('/out')/(arm+'.FCStd')
            doc.saveAs(str(f))
        finally:App.closeDocument(doc.Name)
        doc=App.openDocument(str(f))
        try:
            b=body(doc);s=b.Shape
            dh=sha(f)
            approved=al|{'artifact_frame_approvals':al['artifact_frame_approvals']|{dh:'inherited: verified same fixed body placement and only approved edits; recheck flanks'}}
            checks=validate16(s,rows)
            out[arm].update(sha256=dh,shape_valid=s.isValid(),solid_count=len(s.Solids),volume=s.Volume,
                bbox=[getattr(s.BoundBox,k) for k in ('XMin','XMax','YMin','YMax','ZMin','ZMax')],
                orientation=compare_side(s,dh,approved),checks=checks,signature=signature(doc),
                reopen_faults=status(doc),seconds=time.monotonic()-start)
            copies[arm]=s.copy()
        finally:App.closeDocument(doc.Name)
    old,new=copies['C0'],copies['C1']
    removed=old.cut(new);added=new.cut(old)
    outside_removed=removed.cut(envelope);outside_added=added.cut(envelope)
    def diff(s):
        return dict(volume=s.Volume,bounds=[getattr(s.BoundBox,k) for k in ('XMin','XMax','YMin','YMax','ZMin','ZMax')] if not s.isNull() else None)
    def stage_diffs():
        d0=App.openDocument('/out/C0.FCStd');d1=App.openDocument('/out/C1.FCStd')
        out=[]
        try:
            for f in body(d0).Group:
                if f.TypeId not in ('PartDesign::Pad','PartDesign::Pocket'):continue
                a,b=f.Shape,d1.getObject(f.Name).Shape
                out.append(dict(feature=f.Name,valid_before=a.isValid(),valid_after=b.isValid(),solid_after=len(b.Solids),volume_before=a.Volume,volume_after=b.Volume))
            return out
        finally:
            App.closeDocument(d0.Name);App.closeDocument(d1.Name)
    out['stage_measurements']=stage_diffs()
    a,b=out['C0'],out['C1'];o,n=a['signature'],b['signature']
    changes=[]
    for name,v in o['objects'].items():
        for k,x in v['properties'].items():
            y=n['objects'][name]['properties'][k]
            if x!=y:changes.append(dict(object=name,property=k,before=x,after=y))
    actual={(x['object'],x['property']) for x in changes}
    out['diff']=dict(added=diff(added),removed=diff(removed),outside_added_mm3=outside_added.Volume,outside_removed_mm3=outside_removed.Volume,
        edits=changes,dependency_equal=o['links']==n['links'],tip_equal=o['tip']==n['tip'],group_equal=o['group']==n['group'])
    expected_changes={('UndersideCavityOutline','Placement'),('UndersideCavity','Reversed')}
    gates=dict(control_fail=a['orientation']['verdict']=='FAIL',repaired_pass=b['orientation']['verdict']=='PASS',
        checks_16_both=all(all(r['status']=='PASS' for r in x['checks']) for x in (a,b)),
        solid_both=all(x['shape_valid'] and x['solid_count']==1 and not x['reopen_faults'] for x in (a,b)),
        structure_equal=o['links']==n['links'] and o['tip']==n['tip'] and o['group']==n['group'] and [(k,v['type']) for k,v in o['objects'].items()]==[(k,v['type']) for k,v in n['objects'].items()],
        only_two_fields=actual==expected_changes,
        bbox_preserved=max(abs(x-y) for x,y in zip(a['bbox'],b['bbox']))<.001,
        valid_features=all(f['valid_after'] and f['solid_after']==1 for f in out['stage_measurements']),
        no_outside_delta=outside_removed.Volume<.0001 and outside_added.Volume<.0001)
    out['acceptance']=gates
    p.state('VERIFIED' if all(gates.values()) else 'REJECTED','all gates passed' if all(gates.values()) else 'postcondition failure; C1 not accepted')
    out['proposal']=asdict(p)
    assert sha(path)==h
if __name__=='__main__':
    t=time.monotonic();out={}
    try:
        al=json.loads(Path('/work/alignment.json').read_text())
        synthetic(al,out);process(out)
    finally:
        out['seconds']=time.monotonic()-t
        Path('/out/results.json').write_text(json.dumps(out,indent=2,allow_nan=False))
    print('synthetic',[(k,v['execution_status']) for k,v in out['synthetic'].items()])
    print('proposal',out['proposal']['execution_status'],out['proposal']['events'])
    print('acceptance',out.get('acceptance'))
