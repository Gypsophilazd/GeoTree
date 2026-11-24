"""Evidence-pinned geometry queries. Client suggestions never certify measurement."""
from dataclasses import asdict, dataclass
import hashlib, math, re

@dataclass(frozen=True)
class GeometryQuery:
    constraint_id: str
    measurement_type: str
    correspondence: str
    coordinate_frame: str
    evidence_source: str

FRAME="public layout: x=global X; y=-global Z; extrusion=global +Y"
PLANE="parallel extremal material faces of the unique plate solid"
CENTRAL="unique inward through-cylinder on the symmetry datum in the end extension"
SIDE="two unique inward through-cylinders at the public first side-row anchors"
TRAP="unique noncircular inner wire enclosing the independently stated central opening anchor on both plate skins"
SPECS={
    "plate_thickness":("plane_span",PLANE),
    "plate_datum_y":("material_start",PLANE),
    "center_bore_diameter":("inward_through_diameter",CENTRAL),
    "center_bore_axis_y":("axis_layout_y",CENTRAL),
    "mounting_hole_diameter":("side_row_diameters",SIDE),
    "central_trapezoidal_opening_lower_flat_width":("lowest_horizontal_edge",TRAP),
    "central_trapezoidal_opening_corner_radius":("tangent_corner_radii",TRAP),
}
KEY=re.compile(r"^- ([a-zA-Z0-9_]+) = ([+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)) (mm|degrees)$",re.M)
FRAME_EVIDENCE="Thus layout +x points along global +X, layout +y points along global -Z, and the plate extends from global Y=0 in the +Y direction by plate_thickness."
MAPPING_EVIDENCE="It shares truss_layout_symmetry_axis_x with the outer profile and center bore."
MOUNT_EVIDENCE="The mounting holes and center bore are governed by their respective diameters, pair spacings, rows, and axes."
TRAP_EVIDENCE=("The finished straight lower edge has central_trapezoidal_opening_lower_flat_width.",
  "All six corners are tangent rounds of central_trapezoidal_opening_corner_radius; the named envelope and center locate the complete boundary.")
TOL=.02
MAPPING_TOL=.04

def public_specs(instruction):
    """One deliberately narrow public-text profile; all numerical values are parsed."""
    if not all(x in instruction for x in (FRAME_EVIDENCE,MAPPING_EVIDENCE,MOUNT_EVIDENCE,*TRAP_EVIDENCE)):
        return {},{}
    values={};lines={}
    for m in KEY.finditer(instruction):
        k,v,u=m.groups()
        if k in values:return {},{}
        values[k]=float(v)
        lines[k]=m[0]
    req=set(SPECS)-{"plate_datum_y"}|{"truss_layout_symmetry_axis_x","middle_outer_rectangle_center_y",
        "middle_outer_rectangle_height","small_outer_rectangle_center_y","small_outer_rectangle_height",
        "side_mounting_hole_axis_x","side_mounting_hole_row_1_y","base_sketch_plane_rotation_angle","central_trapezoidal_opening_center_y"}
    if not req<=values.keys() or lines["base_sketch_plane_rotation_angle"].split()[-1]!="degrees" or values["base_sketch_plane_rotation_angle"]!=90:
        return {},{}
    if any(lines[k].split()[-1]!="mm" for k in req-{"base_sketch_plane_rotation_angle"}):return {},{}
    values["plate_datum_y"]=0.
    lines["plate_datum_y"]=FRAME_EVIDENCE
    catalogue={k:GeometryQuery(k,typ,corr,FRAME,lines[k]) for k,(typ,corr) in SPECS.items()}
    return values,catalogue

def validate_query(packet,catalogue):
    if not isinstance(packet,dict) or set(packet)!=set(GeometryQuery.__dataclass_fields__) or not all(isinstance(v,str) and 0<len(v)<=512 for v in packet.values()):
        raise ValueError("invalid GeometryQuery fields")
    q=catalogue.get(packet["constraint_id"])
    if q is None or asdict(q)!=packet:raise ValueError("query not in trusted public catalogue")
    return q

def slab(shape):
    box=shape.BoundBox
    def is_plane(f,y):
        s=f.Surface
        if type(s).__name__!="Plane": return False
        n=s.Axis
        b=f.BoundBox
        return abs(abs(n.y)-1)<1e-6 and max(abs(b.YMin-y),abs(b.YMax-y))<1e-5
    # The single solid must have unambiguous, substantial planar skins at both extrema.
    low=[f for f in shape.Faces if is_plane(f,box.YMin)]
    high=[f for f in shape.Faces if is_plane(f,box.YMax)]
    if len(low)!=1 or len(high)!=1 or box.YLength<=1e-6: return None
    if min(low[0].Area,high[0].Area)<.1*box.XLength*box.ZLength: return None
    if min(box.XLength,box.ZLength)<3*box.YLength: return None
    return box.YMin,box.YMax

def cylinders(shape,y_bounds):
    result=[]
    for idx,f in enumerate(shape.Faces,1):
        s=f.Surface
        if type(s).__name__!="Cylinder" or abs(abs(s.Axis.y)-1)>1e-6:continue
        u0,u1,v0,v1=f.ParameterRange
        u,v=(u0+u1)/2,(v0+v1)/2
        r=f.valueAt(u,v)-s.Center
        radial=r-s.Axis*r.dot(s.Axis)
        if radial.dot(f.normalAt(u,v))>=-1e-6: continue
        bb=f.BoundBox
        full=(u1-u0>=2*math.pi-1e-5 and max(abs(bb.YMin-y_bounds[0]),abs(bb.YMax-y_bounds[1]))<1e-5)
        result.append(dict(face=idx,x=float(s.Center.x),layout_y=-float(s.Center.z),diameter=2*float(s.Radius),full=full))
    return result

def central_loop(shape,bounds,q,values):
    import FreeCAD as A, Part
    x=values["truss_layout_symmetry_axis_x"]
    ly=values["central_trapezoidal_opening_center_y"]
    hits=[]
    for y in bounds:
        faces=[f for f in shape.Faces if type(f.Surface).__name__=="Plane" and
            abs(abs(f.Surface.Axis.y)-1)<1e-6 and max(abs(f.BoundBox.YMin-y),abs(f.BoundBox.YMax-y))<1e-5]
        if len(faces)!=1:return None,hits,"no unique skin"
        f=faces[0]
        inside=[]
        for w in f.Wires:
            if w.isSame(f.OuterWire):continue
            if Part.Face(w).isInside(A.Vector(x,y,-ly),1e-5,False):inside.append(w)
        if len(inside)!=1:return None,hits,"public independent anchor does not uniquely identify inner wire"
        w=inside[0]
        edges=w.Edges
        lines=[e for e in edges if type(e.Curve).__name__=="Line"]
        arcs=[e for e in edges if type(e.Curve).__name__=="Circle"]
        if len(edges)!=12 or len(lines)!=6 or len(arcs)!=6:
            return None,hits,"anchored wire does not map to six straight sides and six distinct arcs"
        if q.measurement_type=="lowest_horizontal_edge":
            lower=[e for e in lines if abs(e.BoundBox.ZMin-e.BoundBox.ZMax)<1e-5 and abs(e.BoundBox.ZMax-w.BoundBox.ZMax)<1e-5]
            if len(lower)!=1:return None,hits,"no unique horizontal edge at the physical lower extremum"
            res=[float(lower[0].Length)]
        else:
            # Radius is independent of tangent validation. Require each arc to connect and
            # be tangent to exactly one straight neighbor at each endpoint.
            for arc in arcs:
                for vertex in arc.Vertexes:
                    point=vertex.Point
                    adj=[line for line in lines if any((p.Point-point).Length<1e-5 for p in line.Vertexes)]
                    if len(adj)!=1:return None,hits,"arc neighbors ambiguous"
                    v=adj[0].Vertexes[1].Point-adj[0].Vertexes[0].Point
                    r=point-arc.Curve.Center
                    if abs(v.dot(r)/(v.Length*r.Length))>1e-5:return None,hits,"arc tangency not established"
            res=sorted(float(e.Curve.Radius) for e in arcs)
        hits.append(dict(y=y,values=res,anchor_layout=[x,ly]))
    a,b=hits
    if any(abs(m-n)>1e-4 for m,n in zip(a["values"],b["values"])):
        return None,hits,"lower/upper skin measurements disagree"
    return (a["values"][0] if q.measurement_type=="lowest_horizontal_edge" else a["values"]),hits,"unique anchored central opening on both plate skins; nominal measured value not used"

def measure(doc,q,values):
    bodies=[o for o in doc.Objects if o.TypeId=="PartDesign::Body"]
    if len(bodies)!=1:return None,[],"no unique body"
    shape=bodies[0].Shape
    if shape.isNull() or not shape.isValid() or len(shape.Solids)!=1:return None,[],"invalid or multiple solids"
    bounds=slab(shape)
    if not bounds:return None,[],"parallel extremal plate faces not uniquely established"
    if q.measurement_type=="plane_span":return bounds[1]-bounds[0],list(bounds),"planar extrema"
    if q.measurement_type=="material_start":return bounds[0],list(bounds),"planar extrema"
    if q.correspondence==TRAP:return central_loop(shape,bounds,q,values)
    holes=cylinders(shape,bounds)
    if q.correspondence==CENTRAL:
        # The selection deliberately does not use the nominal diameter or nominal bore Y.
        lo=values["middle_outer_rectangle_center_y"]+.5*values["middle_outer_rectangle_height"]
        hi=values["small_outer_rectangle_center_y"]+.5*values["small_outer_rectangle_height"]
        cx=values["truss_layout_symmetry_axis_x"]
        match=[f for f in holes if lo <= f["layout_y"] <= hi and abs(f["x"]-cx)<=MAPPING_TOL]
        if len(match)!=1 or not match[0]["full"]:
            return None,match,"central correspondence not unique/full through; absence is not FAIL"
        key="diameter" if q.measurement_type=="inward_through_diameter" else "layout_y"
        return match[0][key],match,"axis-coincident inward through wall in independent end-extension region"
    x=values["side_mounting_hole_axis_x"]
    y=values["side_mounting_hole_row_1_y"]
    sx=values["truss_layout_symmetry_axis_x"]
    groups=[[f for f in holes if abs(f["x"]-ax)<=MAPPING_TOL and abs(f["layout_y"]-y)<=MAPPING_TOL] for ax in (x,2*sx-x)]
    if any(len(g)!=1 or not g[0]["full"] for g in groups):
        return None,groups,"nominal location not uniquely matched; no inferred positional FAIL"
    return [g[0]["diameter"] for g in groups],groups,"matched public row and two symmetrically located axes; diameter unused in selection"

def result(doc,q,values,sha):
    measured,mapping,reason=measure(doc,q,values)
    expected=values[q.constraint_id]
    checks=measured if isinstance(measured,list) else [measured]
    verdict="UNKNOWN" if measured is None else ("PASS" if all(abs(v-expected)<=TOL for v in checks) else "FAIL")
    return dict(query=asdict(q),status=verdict,measured=measured,expected=expected,unit="mm",
        tolerance_mm=TOL,unique_mapping=measured is not None,mapping=mapping,reason=reason,artifact_sha256=sha)

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

e03_public_specs=public_specs
e03_result=result
def public_specs(text):
    v,c=e03_public_specs(text)
    return v,c|right_catalogue(text, GeometryQuery)
def result(doc,q,v,sha):
    if q.measurement_type==RIGHT_KIND:
        from pathlib import Path
        return right_measure(doc,q,Path("/in/instruction.md").read_text(),sha,slab)
    return e03_result(doc,q,v,sha)
