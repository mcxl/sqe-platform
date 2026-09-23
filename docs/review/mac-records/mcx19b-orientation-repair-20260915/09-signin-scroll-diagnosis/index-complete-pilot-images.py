from pathlib import Path
import json,hashlib,struct,time,datetime,os
os.umask(0o077)
stage=Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915')
d=stage/'09-signin-scroll-diagnosis'
runs=list((d/'complete-pilot-runs').glob('*-pilot-*'));assert len(runs)==1,runs
run=runs[0]
output=d/'complete-pilot-image-review';output.mkdir(mode=0o700,exist_ok=True)
start=time.monotonic();images=[];batches=[]
for checkpoint in sorted((run/'batches').glob('*/checkpoint.json')):
 d=json.loads(checkpoint.read_text());assert d['status']=='passed'
 batch=checkpoint.parent;record=d['record'];case_ids={c['id'] for c in record['caseRecords']};batches.append(batch.name)
 manifest=json.loads((batch/'attachments/manifest.json').read_text())
 exported={a['exportedFileName']:a for test in manifest for a in test.get('attachments',[])}
 for p in sorted((batch/'attachments').glob('*.png')):
  raw=p.read_bytes();assert raw[:8]==b'\x89PNG\r\n\x1a\n'
  item=exported.get(p.name);assert item is not None,p
  name=item.get('suggestedHumanReadableName','')
  case_id=name.removeprefix('Coverage ').split(' viewport ',1)[0] if name.startswith('Coverage ') and ' viewport ' in name else None
  if case_id is not None:assert case_id in case_ids,case_id
  images.append({'path':str(p),'batch':batch.name,'caseId':case_id,'nativeName':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'dimensions':list(struct.unpack('>II',raw[16:24]))})
groups={}
for item in images:groups.setdefault(item['sha256'],[]).append(item)
result={'run':str(run),'candidateCommit':'c8b10875658e5fbd6a66dea1fbcec9bb4a2f5b0d','indexedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'completedBatches':batches,'nativeCaptureCount':len(images),'uniqueImageCount':len(groups),'collectionSeconds':round(time.monotonic()-start,3),'images':images,'uniqueImages':[{'sha256':h,'representative':items[0],'allCapturePaths':[i['path'] for i in items],'caseIds':sorted({i['caseId'] for i in items if i['caseId']})} for h,items in groups.items()]}
(output/'image-index.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k not in ['images','uniqueImages']}))
