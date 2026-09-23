from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,tarfile,os,time,subprocess
os.umask(0o077)
stage=Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915')
assert not subprocess.run(['pgrep','-x','xcodebuild'],capture_output=True,text=True).stdout.strip(), 'Native execution still active'
started=time.monotonic()
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
archive=stage.parent/('mcx19b-orientation-pilot-evidence-'+stamp+'.tar.gz')
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
files=[];excluded=[]
for root,dirs,names in os.walk(stage,followlinks=False):
 root=Path(root)
 keep=[]
 for name in dirs:
  p=root/name
  if name=='build' or name=='__pycache__' or (p/'.git').exists() or (root==stage and 'worktree' in name) or p.is_symlink():
   excluded.append(str(p.relative_to(stage)))
  else:keep.append(name)
 dirs[:]=keep
 for name in names:
  p=root/name
  if p.is_symlink():raise RuntimeError('Unexpected evidence symlink: '+str(p))
  if p.suffix=='.pyc' or name.endswith('.tar.gz'):continue
  files.append(p)
files.sort()
index={str(p.relative_to(stage)):{'bytes':p.stat().st_size,'sha256':digest(p)} for p in files}
with tarfile.open(archive,'x:gz',compresslevel=1) as target:
 for p in files:target.add(p,arcname=str(p.relative_to(stage)),recursive=False)
archive.chmod(0o600)
with tarfile.open(archive,'r:gz') as source:
 members=source.getmembers()
 assert len(members)==len(index)
 for member in members:
  assert member.isfile() and member.name in index
  h=hashlib.sha256()
  with source.extractfile(member) as stream:
   for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
  assert member.size==index[member.name]['bytes'] and h.hexdigest()==index[member.name]['sha256'],member.name
now=datetime.now(timezone.utc)
record={'archive':str(archive),'archiveBytes':archive.stat().st_size,'archiveSha256':digest(archive),'memberCount':len(index),'rawBytes':sum(x['bytes'] for x in index.values()),'allMemberHashesVerified':True,'verifiedUTC':now.isoformat(),'retainUntilAtLeastUTC':(now+timedelta(days=30)).isoformat(),'automaticDeletion':False,'seconds':round(time.monotonic()-started,3),'stageMode':oct(stage.stat().st_mode&0o777),'archiveMode':oct(archive.stat().st_mode&0o777),'excludedPreservedDirectories':excluded,'files':index,'retrievalStatus':'Pending independent authenticated stream verification'}
result=stage/('archive-verification-'+stamp+'.json')
with result.open('x') as stream:json.dump(record,stream,indent=2)
print(json.dumps({k:v for k,v in record.items() if k!='files'}),flush=True)
print('record='+str(result),flush=True)
