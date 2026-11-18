"""Untrusted discovery; only the separate evidence gate grants authority."""
from dataclasses import dataclass, asdict
import hashlib, math, re

@dataclass(frozen=True)
class ConstraintCandidate:
    constraint_id: str
    constraint_type: str
    expected_value: float | None
    unit: str
    evidence_type: str
    source_text: str | None
    image_roi: tuple | None
    coordinate_frame: str | None
    proposed_feature_mapping: dict
    uncertainty: str
    validation_status: str = 'CANDIDATE'
    source_span: tuple | None = None

NUM=r'[+-]?(?:\d+(?:\.\d+)?|\.\d+)'
PARAM=re.compile(r'^\s*[-*]\s+([a-z][a-z0-9_]*)\s*=\s*('+NUM+r')\s*(mm|degrees?|°)\s*$',re.M|re.I)
EXPLICIT=(
 ('bbox',r'Overall ([XYZ]) (?:extent|length)\s*(?:=|is)\s*('+NUM+r')\s*mm\.?'),
 ('pad_length',r'Set ([A-Za-z][A-Za-z0-9_]*)\.Length to ('+NUM+r')\s*mm\.?'),
 ('feature_present',r'Require one (PartDesign::(?:Pad|Pocket|Hole))\.?'),
 ('bore_position',r'Bore center at X\s*=\s*('+NUM+r')\s*mm, Y\s*=\s*('+NUM+r')\s*mm\s+in the XY plane\.?'))
BODY=r'(?:exactly one|a single|single) PartDesign Body'
SOLID=r'(?:producing exactly one solid body|produces a single solid)'

def digest(s):
    return hashlib.sha256(s.encode() if isinstance(s,str) else s).hexdigest()

def extract_text(instruction):
    if not isinstance(instruction,str) or len(instruction)>50000:raise ValueError('instruction size')
    out=[]
    def add(match,key,kind,v,unit,frame,mapping,uncertainty=''):
        if v is not None and not math.isfinite(v):return
        out.append(ConstraintCandidate(key,kind,v,unit,'PUBLIC_TEXT',match[0],None,frame,mapping,uncertainty,source_span=match.span()))
    for kind,pattern in EXPLICIT:
        for m in re.finditer(r'^'+pattern+r'$',instruction,re.M):
            if kind=='bbox':add(m,'extent_'+m[1],kind,float(m[2]),'mm','artifact XYZ',{'axis':m[1]})
            elif kind=='pad_length':add(m,m[1]+'.Length',kind,float(m[2]),'mm','artifact XYZ',{'feature':m[1]})
            elif kind=='feature_present':add(m,m[1],kind,1,'count',None,{'type_id':m[1]})
            else:add(m,'bore_xy',kind,None,'mm','XY (Z-axis bore)',{'xy':[float(m[1]),float(m[2])]},'requires independent bore identity')
    for pattern,kind in ((BODY,'body_count'),(SOLID,'solid_count')):
        for m in re.finditer(pattern,instruction,re.I):add(m,kind,kind,1,'count',None,{})
    for m in PARAM.finditer(instruction):
        key=m[1]; v=float(m[2]); unit='mm' if m[3].lower()=='mm' else 'deg'
        semantic='angle' if unit=='deg' else 'diameter' if key.endswith('_diameter') else 'length'
        add(m,key,semantic,v,unit,None,{'parameter':key},'explicit value; geometric role not established')
    # Narrow public-language rule: body explicitly characterized as a solid cylinder,
    # with two named parameters directly tied to its outer diameter and axial thickness.
    role=re.search(r'The body has ([a-z_]+_outer_diameter) and ([a-z_]+_thickness) and is centered about its axial mid-plane\.',instruction)
    if role and re.search(r'\bsolid cylindrical body\b',instruction,re.I):
        for i,kind in [(1,'round_body_diameter'),(2,'round_body_thickness')]:
            options=[m for m in PARAM.finditer(instruction) if m[1]==role[i] and m[3].lower()=='mm']
            if len(options)==1:
                out=[x for x in out if x.constraint_id!=role[i]]
                add(options[0],role[i],kind,float(options[0][2]),'mm','unique full external cylindrical envelope axis',
                    {'role_span':role.span(),'role_text':role[0]})
    return out

MODEL_TYPES={'bbox','length','diameter','angle','feature_present','bore_position','pad_length','other'}
async def propose_drawing(provider,instruction,image_sha256,image_size):
    """Provider adapter resolves the approved image attachment by hash, never by model path."""
    reply=await provider.propose(dict(kind='constraint_candidates',instruction=instruction,
        image_sha256=image_sha256,image_size=image_size,max_candidates=12,
        response='candidates[{constraint_id,constraint_type,expected_value,unit,image_roi,coordinate_frame,uncertainty}]'))
    packet=reply.payload
    if not isinstance(packet,dict) or set(packet)!={'candidates'} or not isinstance(packet['candidates'],list) or len(packet['candidates'])>12:
        raise ValueError('candidate envelope')
    out=[]
    fields={'constraint_id','constraint_type','expected_value','unit','image_roi','coordinate_frame','uncertainty'}
    for x in packet['candidates']:
        if not isinstance(x,dict) or set(x)!=fields:raise ValueError('candidate fields; authority and commands forbidden')
        roi=x['image_roi'];v=x['expected_value']
        if not isinstance(roi,list) or len(roi)!=4 or any(type(a) is not int for a in roi) or not (0<=roi[0]<roi[2]<=image_size[0] and 0<=roi[1]<roi[3]<=image_size[1]):raise ValueError('ROI')
        if type(v) not in (int,float) or not math.isfinite(v):raise ValueError('nonfinite value')
        if any(not isinstance(x[k],str) or len(x[k])>160 for k in ('constraint_id','constraint_type','unit','coordinate_frame','uncertainty')):raise ValueError('text fields')
        if x['constraint_type'] not in MODEL_TYPES or x['unit'] not in ('mm','deg','count'):raise ValueError('unsupported schema unit or type')
        out.append(ConstraintCandidate(x['constraint_id'],x['constraint_type'],float(v),x['unit'],'MODEL_IMAGE',None,tuple(roi),
          x['coordinate_frame'],{},x['uncertainty']))
    return out,reply.usage
