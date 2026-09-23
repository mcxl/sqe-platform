from pathlib import Path
import json,hashlib,tarfile,datetime,time
stage=Path('LOCAL_HOME/ace-private/mcx19b-complete-pilot-20260915')
run=stage/'pilot-runs/20260915T045947Z-pilot-84db4f8f536f'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
started=time.monotonic()
files=[p for p in run.rglob('*') if p.is_file() and not p.is_relative_to(run/'build')]
files += [p for p in (stage/'failure-video-frames').rglob('*') if p.is_file()]
files += [stage/n for n in ('TASK.json','RESULT.json','RESULT.md','final-state.json','failure-video-inspection.json','resource-observations.jsonl','pilot-command.json','pilot-console.log','run-pilot.py','extract-failure-frames.swift') if (stage/n).is_file()]
files=sorted(set(files)); index={str(p.relative_to(stage)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in files}
archive=stage/'native-pilot-evidence.tar.gz'
with tarfile.open(archive,'x:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(stage)),recursive=False)
archive.chmod(0o600)
with tarfile.open(archive,'r:gz') as tar:
 members=tar.getmembers();assert len(members)==len(index)
 for m in members:
  h=hashlib.sha256();f=tar.extractfile(m)
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
  assert m.size==index[m.name]['bytes'] and h.hexdigest()==index[m.name]['sha256'],m.name
now=datetime.datetime.now(datetime.timezone.utc)
result={'archive':str(archive),'bytes':archive.stat().st_size,'sha256':sha(archive),'memberCount':len(index),'allMemberHashesVerified':True,'files':index,'archiveAndVerificationSeconds':round(time.monotonic()-started,3),'verifiedUTC':now.isoformat(),'retainUntilAtLeastUTC':(now+datetime.timedelta(days=30)).isoformat(),'automaticDeletion':False,'protectedOriginalRun':str(run),'protectedBuildProducts':str(run/'build'),'privateStageMode':oct(stage.stat().st_mode & 0o777),'archiveMode':oct(archive.stat().st_mode & 0o777)}
(stage/'archive-verification.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='files'}))
