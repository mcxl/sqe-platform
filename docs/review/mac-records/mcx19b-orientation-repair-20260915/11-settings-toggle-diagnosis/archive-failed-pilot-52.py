from pathlib import Path
import datetime, gzip, hashlib, json, os, subprocess, tarfile
base=Path("LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915/11-settings-toggle-diagnosis")
run=base/"complete-pilot-runs/20260915T133932Z-pilot-497a5a280dc6"
assert subprocess.run(["pgrep","-x","xcodebuild"],capture_output=True).returncode==1
archiveDir=Path("LOCAL_HOME/ace-private/mcx19b-archives")
archiveDir.mkdir(mode=0o700,exist_ok=True)
assert not archiveDir.is_symlink() and archiveDir.stat().st_mode & 0o077 == 0
archive=archiveDir/"failed-pilot-52b212a-20260915T133932Z.tar.gz"
files={}
for p in run.rglob("*"):
    assert not p.is_symlink(), str(p)
    if p.is_file(): files["run/"+str(p.relative_to(run))]=p
for name in ["copy-failure-52b212a.json","failed-pilot-image-inspection-52b212a.json","complete-pilot-execution.json","complete-pilot-build.json","clean-candidate.json"]:
    p=base/name
    assert p.is_file() and not p.is_symlink()
    files["records/"+name]=p
manifest={name:{"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for name,p in files.items()}
started=datetime.datetime.now(datetime.timezone.utc)
fd=os.open(archive,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,"wb") as raw:
    with gzip.GzipFile(filename="",mode="wb",compresslevel=1,fileobj=raw,mtime=0) as compressed:
        with tarfile.open(fileobj=compressed,mode="w") as tf:
            for name,p in sorted(files.items()): tf.add(p,arcname=name,recursive=False)
with tarfile.open(archive,"r:gz") as tf:
    members=tf.getmembers()
    assert len(members)==len(manifest)
    for member in members:
        assert member.isfile() and member.name in manifest
        data=tf.extractfile(member).read()
        assert len(data)==manifest[member.name]["bytes"]
        assert hashlib.sha256(data).hexdigest()==manifest[member.name]["sha256"]
finished=datetime.datetime.now(datetime.timezone.utc)
record={"status":"passed","purpose":"Preserve the failed 52b212a pilot and its inspected evidence. This is not a passing pilot.","startedUTC":started.isoformat(),"finishedUTC":finished.isoformat(),"archive":str(archive),"archiveBytes":archive.stat().st_size,"archiveSha256":hashlib.sha256(archive.read_bytes()).hexdigest(),"memberCount":len(manifest),"sourceBytes":sum(x["bytes"] for x in manifest.values()),"retainUntilAtLeastUTC":(finished+datetime.timedelta(days=30)).isoformat(),"deletionScheduled":False,"mode":oct(archive.stat().st_mode & 0o777),"members":manifest}
out=base/"failed-pilot-archive-verification-52b212a.json"
with out.open("x") as f: json.dump(record,f,indent=2); f.write("\n")
print(json.dumps({k:v for k,v in record.items() if k!="members"},indent=2))
