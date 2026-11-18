"""Offline E02-H. OpenDocument only for read-only copies, no scorer or model."""
import hashlib,json,math,time
from pathlib import Path
import FreeCAD as App, Part, TechDraw, Sketcher
V=App.Vector
FRAMES={
 'front':((1,0,0),(0,0,1),(0,-1,0)),
 'top':((1,0,0),(0,1,0),(0,0,1)),
 'bottom':((1,0,0),(0,-1,0),(0,0,-1)),
 'left':((0,-1,0),(0,0,1),(-1,0,0))}
def project(shape,name):
    r=App.Rotation(*(V(*v) for v in FRAMES[name]),'ZXY')
    transformed=shape.copy()
    transformed.transformShape(r.inverted().toMatrix())
    parts=TechDraw.project(transformed,V(0,0,1))
    assert len(parts)==4
    out={}
    for key,group in zip(('visible_G0','visible_G1','hidden_G0','hidden_G1'),parts):
        out[key]=[[(float(p.x),float(p.y)) for p in e.discretize(Deflection=.04)] for e in group.Edges]
    return out
def rim(layer):
    # Near both dimensioned long straight cavity walls, not at a hole/fillet.
    def witness(y):
        for line in layer:
            for a,b in zip(line,line[1:]):
                if max(abs(a[1]-y),abs(b[1]-y))<.07 and min(a[0],b[0])<=43 and max(a[0],b[0])>=47:
                    return True
        return False
    return [witness(-16),witness(16)]
def svg(data,title):
    paths=[]
    for k,ls in data.items():
        if not k.endswith('G0'):continue
        for line in ls:
            if len(line)<2:continue
            coords=' '.join(f'{x:.4f},{-y:.4f}' for x,y in line)
            style='stroke="#98a0a8" stroke-width=".18" stroke-dasharray="1.2 .65"' if k.startswith('hidden') else 'stroke="#124879" stroke-width=".27"'
            paths.append(f'<polyline fill="none" {style} points="{coords}"/>')
    pts=[p for g in data.values() for l in g for p in l]
    x0,x1=min(x for x,y in pts)-3,max(x for x,y in pts)+3
    y0,y1=min(-y for x,y in pts)-3,max(-y for x,y in pts)+3
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {x1-x0} {y1-y0}"><title>{title}</title>'+''.join(paths)+'</svg>'
def intervals(s,x,y):
    probe=s.common(Part.makeLine(V(x,y,-2),V(x,y,42)))
    return sorted([[float(e.BoundBox.ZMin),float(e.BoundBox.ZMax)] for e in probe.Edges])
def compare(s,digest,align,hlr=None):
    result=dict(constraint_id='main_cavity_opening_side',public_source=align.get('public_source'),
      view_alignment_evidence=align.get('view_alignment_evidence',[]),expected_relation=align.get('target',{}).get('expected_relation'),
      measured_relation=None,artifact_hash=digest,mapping_status='unverified',verdict='UNKNOWN',uncertainty_reason=None)
    if digest not in align.get('artifact_frame_approvals',{}):
        return result|{'uncertainty_reason':'artifact_requires_frame_review'}
    if result['expected_relation'] not in ('TOP','BOTTOM'):
        return result|{'uncertainty_reason':'target_view_direction_unconfirmed'}
    if not s.isValid() or len(s.Solids)!=1:
        return result|{'uncertainty_reason':'no_valid_unique_solid'}
    hlr=hlr or {n:project(s,n) for n in ('top','bottom')}
    report={n:{k:rim(v) for k,v in h.items() if k.endswith('G0')} for n,h in hlr.items() if n in ('top','bottom')}
    xs=(35,45,55)
    rows={str(x):intervals(s,x,0) for x in xs}
    flanks={str(y):intervals(s,45,y) for y in (-18,18)}
    def close(a,b):return abs(a-b)<.02
    if not all(len(q)==1 and close(q[0][0],0) and close(q[0][1],28) for q in flanks.values()):
        return result|dict(uncertainty_reason='no_local_28mm_deck_witness',geometry_evidence=dict(rim=report,centerlines=rows,flanks=flanks))
    top=all(len(q)==1 and close(q[0][0],0) and .05<q[0][1]<27.95 for q in rows.values())
    bottom=all(len(q)==1 and close(q[0][1],28) and .05<q[0][0]<27.95 for q in rows.values())
    top=top and all(report['top']['visible_G0']) and all(report['bottom']['hidden_G0']) and not any(report['bottom']['visible_G0'])
    bottom=bottom and all(report['bottom']['visible_G0']) and all(report['top']['hidden_G0']) and not any(report['top']['visible_G0'])
    e=dict(rim=report,centerlines=rows,flanks=flanks)
    if top==bottom:return result|dict(uncertainty_reason='no_unique_rim_and_occupancy_orientation',geometry_evidence=e)
    relation='TOP' if top else 'BOTTOM'
    return result|dict(measured_relation=relation,mapping_status='reviewed_public_alignment_and_confirmed_local_geometry',verdict='PASS' if relation==result['expected_relation'] else 'FAIL',geometry_evidence=e)
def fixture(side):
    doc=App.newDocument()
    b=doc.addObject('PartDesign::Body','Body')
    def rect(name,xx,yy,z):
        s=b.newObject('Sketcher::SketchObject',name);s.Placement.Base=V(0,0,z)
        p=[V(x,y,0) for x,y in ((xx[0],yy[0]),(xx[1],yy[0]),(xx[1],yy[1]),(xx[0],yy[1]))]
        s.addGeometry([Part.LineSegment(p[i],p[(i+1)%4]) for i in range(4)],False);return s
    pad=b.newObject('PartDesign::Pad','Pad');pad.Profile=rect('Block',(0,141),(-25.4,25.4),0);pad.Length=28;doc.recompute()
    cut=b.newObject('PartDesign::Pocket','Pocket');cut.Profile=rect('Cavity',(5,110),(-16,16),28 if side=='TOP' else 0)
    cut.Reversed=side=='BOTTOM';cut.Length=22;doc.recompute();return doc,b.Shape
def main():
    al=json.loads(Path('/work/alignment.json').read_text());out={'freecad':'.'.join(App.Version()[:3]),'historical':{},'tests':{}}
    for arm in ('a0','a1'):
        p=Path('/inputs')/(arm+'.FCStd');h=hashlib.sha256(p.read_bytes()).hexdigest()
        doc=App.openDocument(str(p));t=time.monotonic()
        try:
            body,=[o for o in doc.Objects if o.TypeId=='PartDesign::Body'];s=body.Shape
            hlr={n:project(s,n) for n in FRAMES}
            for n,x in hlr.items():Path(f'/out/{arm}-{n}.svg').write_text(svg(x,f'{arm} {n} orthographic HLR'))
            row=compare(s,h,al,hlr);row['body']=body.Name;row['hlr_counts']={n:{k:len(v) for k,v in x.items()} for n,x in hlr.items()}
            row['seconds']=time.monotonic()-t;out['historical'][arm]=row
        finally:App.closeDocument(doc.Name)
        assert hashlib.sha256(p.read_bytes()).hexdigest()==h
    for side,expected in [('TOP','PASS'),('BOTTOM','FAIL')]:
        doc,s=fixture(side)
        try:
            assert s.isValid() and len(s.Solids)==1
            test_al=al|{'artifact_frame_approvals':{'fixture':'fixture frame'}}
            row=compare(s,'fixture',test_al);out['tests'][side]=row
            if side=='TOP':
                out['tests']['ambiguous_target']=compare(s,'fixture',test_al|{'target':{}})
                reflected=s.mirror(V(0,0,14),V(0,0,1))
                out['tests']['unregistered_reflection']=compare(reflected,'fixture-mirrored',test_al)
                out['tests']['registered_reflection']=compare(reflected,'fixture-mirrored',test_al|{'artifact_frame_approvals':{'fixture-mirrored':'explicit retained world frame'}})
        finally:App.closeDocument(doc.Name)
    Path('/out/result.json').write_text(json.dumps(out,indent=2))
    actual={k:v['verdict'] for k,v in out['tests'].items()}
    assert actual==dict(TOP='PASS',BOTTOM='FAIL',ambiguous_target='UNKNOWN',unregistered_reflection='UNKNOWN',registered_reflection='FAIL'),actual
    print('PASS controls:',actual)
    for k,v in out['historical'].items():print(k,v['verdict'],v.get('geometry_evidence'),v.get('uncertainty_reason'))
if __name__=='__main__':main()
