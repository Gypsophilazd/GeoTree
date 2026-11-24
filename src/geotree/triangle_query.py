"""Typed public frame and right-angle measurement on the straight support lines."""
import math,re,itertools
from dataclasses import asdict

RIGHT_KIND='triangle_right_angle'
RIGHT_ID='right_triangular_opening_01_orthogonality'
OLD_PROSE='The two right triangles and the small triangle have lower horizontal bases and upward apices.'
OLD_FRAME='Thus layout +x points along global +X, layout +y points along global -Z, and the plate extends from global Y=0 in the +Y direction by plate_thickness.'
NEW_FRAME=re.compile(r'^Layout frame: origin=\(([-0-9., ]+)\) mm; x=([+-][XYZ]); y=([+-][XYZ]); normal=([+-][XYZ])\.$',re.M)
NEW_FEATURE=re.compile(r'^Opening ([a-z][a-z0-9_]{0,63}) shall be a right triangle; public witness=\(([-0-9., ]+)\) mm; search radius=([0-9.]+) mm\.$',re.M)
TOL_DEG=.05

def parse_right(text):
    def coords(raw,n):
        x=tuple(map(float,raw.split(',')))
        if len(x)!=n or any(not math.isfinite(v) or abs(v)>100000 for v in x):raise ValueError('coordinate range')
        return x
    frames=list(NEW_FRAME.finditer(text))
    if frames:
        if len(frames)!=1:return {}
        f=frames[0]
        try:o=coords(f[1],3)
        except ValueError:return {}
        axes=tuple(f[i] for i in (2,3,4))
        if len({a[1] for a in axes})!=3:return {}
        features=list(NEW_FEATURE.finditer(text))
        if len({m[1] for m in features})!=len(features):return {}
        result={}
        for m in features:
            try:w=coords(m[2],2);r=float(m[3])
            except ValueError:continue
            if 0<=r<=100:
                result[m[1]]=dict(origin=o,axes=axes,witness=w,radius=r,frame=f[0],source=m[0])
        return result
    if OLD_FRAME not in text or OLD_PROSE not in text:return {}
    raw=[]
    for suffix in ('x','y'):
        m=re.findall(r'^- right_triangular_opening_01_centroid_'+suffix+r' = ([-0-9.]+) mm$',text,re.M)
        if len(m)!=1:return {}
        raw.append(m[0])
    try:w=coords(','.join(raw),2)
    except ValueError:return {}
    return {RIGHT_ID:dict(origin=(0.,0.,0.),axes=('+X','-Z','+Y'),witness=w,radius=0.,frame=OLD_FRAME,
        source=OLD_PROSE+' Public witness layout coordinates: '+','.join(raw)+' mm.')}

def right_catalogue(text,query_type):
    return {k:query_type(k,RIGHT_KIND,'unique inner wire at independently published witness on each skin',
        v['frame'],v['source']) for k,v in parse_right(text).items()}

def right_measure(doc,q,text,sha,slab):
    import FreeCAD as A,Part
    def out(status,why,rows=(),unique=False):
        return dict(query=asdict(q),status=status,reason=why,unique_mapping=unique,mapping=rows,
          measured=max(rows[0]['acute_deg']) if rows else None,expected=90.,unit='deg',tolerance_deg=TOL_DEG,artifact_sha256=sha)
    spec=parse_right(text).get(q.constraint_id)
    if not spec:return out('NOT_CHECKABLE','invalid or unsupported public frame / evidence')
    def axis(s):
        v=[0.,0.,0.];v['XYZ'.index(s[1])]=1. if s[0]=='+' else -1.;return A.Vector(*v)
    u,v,n=map(axis,spec['axes'])
    if (u.cross(n)+v).Length>1e-6:return out('NOT_CHECKABLE','frame handedness unsupported')
    b=[x for x in doc.Objects if x.TypeId=='PartDesign::Body']
    if len(b)!=1:return out('UNKNOWN','no unique body')
    sh=b[0].Shape.copy()
    if sh.isNull() or not sh.isValid() or len(sh.Solids)!=1:return out('UNKNOWN','not a single valid solid')
    matrix=A.Matrix()
    origin=A.Vector(*spec['origin'])
    for row,a in enumerate((u,n,-v),1):
        for col,value in enumerate((a.x,a.y,a.z,-a.dot(origin)),1):
            setattr(matrix,f'A{row}{col}',value)
    sh.transformShape(matrix)
    skins=slab(sh)
    if not skins:return out('UNKNOWN','public frame does not identify two unique slab skins')
    rows=[]
    for y in skins:
        faces=[f for f in sh.Faces if type(f.Surface).__name__=='Plane' and abs(abs(f.Surface.Axis.y)-1)<1e-6 and
          max(abs(f.BoundBox.YMin-y),abs(f.BoundBox.YMax-y))<1e-5]
        if len(faces)!=1:return out('UNKNOWN','skin identity')
        face=faces[0]
        x,ly=spec['witness'];point=A.Vector(x,y,-ly)
        hits=[w for w in face.Wires if not w.isSame(face.OuterWire) and
              Part.Face(w).distToShape(Part.Vertex(point))[0]<=spec['radius']+1e-5]
        if len(hits)!=1:return out('UNKNOWN',f'{len(hits)} witnesses matched on one skin; never choose by angle')
        es=hits[0].Edges
        lines=[e for e in es if type(e.Curve).__name__=='Line' and len(e.Vertexes)==2]
        arcs=[e for e in es if type(e.Curve).__name__=='Circle']
        if len(lines)!=3 or len(arcs) not in (0,3) or len(es)!=len(lines)+len(arcs):
            return out('NOT_CHECKABLE','wire not a sharp or three-rounded supporting triangle')
        dirs=[e.Vertexes[1].Point-e.Vertexes[0].Point for e in lines]
        if any(d.Length<1e-5 for d in dirs):return out('NOT_CHECKABLE','degenerate edge')
        def pt(v):return (round(float(v.x),7),round(float(-v.z),7))
        ends=sorted(tuple(sorted(pt(v.Point) for v in e.Vertexes)) for e in lines)
        angles=sorted(math.degrees(math.acos(min(1.,abs(a.dot(b)/(a.Length*b.Length))))) for a,b in itertools.combinations(dirs,2))
        if min(angles)<1e-4:return out('NOT_CHECKABLE','parallel support lines')
        rows.append(dict(skin=float(y),support_segments=ends,acute_deg=angles,arc_count=len(arcs)))
    delta=max(abs(a-b) for s,t in zip(rows[0]['support_segments'],rows[1]['support_segments']) for p,q in zip(s,t) for a,b in zip(p,q))
    if delta>1e-4 or rows[0]['arc_count']!=rows[1]['arc_count']:
        return out('UNKNOWN','projected support endpoints differ across skins')
    return out('PASS' if 90-max(rows[0]['acute_deg'])<=TOL_DEG else 'FAIL',
        'unique public anchor; matched projected support lines on both skins',rows,True)
