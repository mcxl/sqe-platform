from pathlib import Path
import subprocess,json,datetime
root=Path("LOCAL_HOME/Developer/sqe-platform-release-layout")
ev=Path("LOCAL_HOME/ace-private/mcx19b-implementation-20260914/pilot-preparation-20260915")
args=["/Library/Frameworks/Python.framework/Versions/3.14/bin/python3",str(root/"tools/ace_ios_local.py"),"--evidence-root",str(ev/"pilot-runs"),"pilot","--pocock-evidence",str(ev/"pocock-readiness-b2c4509.json"),"--functional-evidence",str(ev/"functional-readiness-b2c4509.json"),"--evidence-gate",str(ev/"evidence-gate-readiness-b2c4509.json"),"--private-input-record",str(ev/"private-input-readiness-b2c4509.json")]
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
r=subprocess.run(args,cwd=root,capture_output=True,text=True)
(ev/"native-pilot-console.log").write_text(r.stdout+r.stderr)
record={"command":args,"startedUTC":start,"finishedUTC":datetime.datetime.now(datetime.timezone.utc).isoformat(),"runnerExit":r.returncode,"stdout":r.stdout,"stderr":r.stderr}
(ev/"native-pilot-command.json").write_text(json.dumps(record,indent=2))
print(json.dumps(record),flush=True)
raise SystemExit(r.returncode)
