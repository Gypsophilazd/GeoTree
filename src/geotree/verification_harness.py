"""Optional NoSearch glue; trusted callbacks resolve artifacts and enforce execution policy."""
from .constraint_candidates import extract_text,digest
from dataclasses import asdict

def disposition(report):
    if report['artifact_status']!='VALID':return 'REQUEST_INSPECTION'
    if any(r['hard_fail'] for r in report['results']):return 'PROPOSE_REPAIR'
    if report['results'] and all(r['status']=='PASS' for r in report['results']):return 'DONE_ELIGIBLE'
    return 'REQUEST_INSPECTION'

class VerificationExecutor:
    def __init__(self,base,inspect,instruction,repair=None):
        self.base=base;self.inspect=inspect;self.repair=repair;self.public_sha=digest(instruction)
    def bound(self,r):
        return all(x['public_sha256']==self.public_sha and x['artifact_sha256']==r['artifact_sha256'] for x in r['results'])
    async def execute(self,p):
        raw=dict(await self.base.execute(p))
        if p.action!='run_freecad' or raw.get('exit_status')!=0:return raw
        report=await self.inspect()
        if not self.bound(report):
            return raw|{'task_grounded':{'disposition':'REQUEST_INSPECTION','error':'observation_binding_mismatch'}}
        choice=disposition(report)
        summary=dict(report=report,disposition=choice)
        if choice=='PROPOSE_REPAIR' and self.repair is not None:
            rr=await self.repair(report)
            req=rr.get('request',{})
            ids={r['candidate']['constraint_id'] for r in report['results'] if r['hard_fail']}
            if req.get('artifact_sha256')!=report['artifact_sha256'] or req.get('public_sha256')!=self.public_sha or req.get('constraint_id') not in ids:
                summary.update(disposition='REQUEST_INSPECTION',error='repair_binding_mismatch')
            else:
                summary['repair']=rr
                post=rr.get('post')
                if rr['status']=='VERIFIED' and post and post['artifact_sha256']==rr.get('output_sha256') and self.bound(post):
                    summary['disposition']=disposition(post)
                else:summary['disposition']='REQUEST_INSPECTION'
        raw['task_grounded']=summary
        return raw

class PublicConstraintProvider:
    """Legacy provider interface. Only supplies candidates, not authority."""
    def __init__(self,base,instruction,image_candidates=()):
        self.base=base;self.candidates=[asdict(x) for x in [*extract_text(instruction),*image_candidates]]
    async def propose(self,obs):
        return await self.base.propose(dict(obs,public_constraint_candidates=self.candidates))
