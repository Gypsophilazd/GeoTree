"""Server-only Responses SSE adapter. Paid requests require explicit operator opt-in."""
import json,os,urllib.request
def available():return bool(os.getenv('DEEPSEEK_API_KEY') and os.getenv('GEOTREE_DEEPSEEK_APPROVED')=='1')
def call(prompt,emit,transport=urllib.request.urlopen,key=None):
 if key is None:
  if not available():raise RuntimeError('DeepSeek NOT_CONFIGURED or not authorized')
  key=os.environ['DEEPSEEK_API_KEY']
 payload={'model':'deepseek-flash','input':prompt,'stream':True}
 req=urllib.request.Request('https://api.deepseek.com/responses',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','Accept':'text/event-stream'})
 final=None;parts=[]
 with transport(req,timeout=90) as stream:
  for raw in stream:
   if not raw.startswith(b'data: '):continue
   s=raw[6:].strip()
   if s==b'[DONE]':break
   e=json.loads(s);t=e.get('type')
   if t=='response.output_text.delta':parts.append(e['delta']);emit('response.output_text.delta',{'characters':len(e['delta'])})
   elif t=='response.completed':final=e['response']
   elif t in ('error','response.failed','response.incomplete'):raise RuntimeError(t)
 if final is None:raise RuntimeError('DeepSeek stream missing completion')
 if not parts:parts=[c['text'] for o in final.get('output',[]) for c in o.get('content',[]) if c.get('type')=='output_text']
 return json.loads(''.join(parts)),final.get('usage',{}),final.get('model','unreported')
