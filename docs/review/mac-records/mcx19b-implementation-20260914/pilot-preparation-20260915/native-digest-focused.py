from pathlib import Path
import subprocess,json,datetime
root=Path("LOCAL_HOME/Developer/sqe-platform-release-layout")
ev=Path("LOCAL_HOME/ace-private/mcx19b-implementation-20260914/pilot-preparation-20260915")
selectors=["ACEClientAppTests/AcceptanceEvidenceContractTests/testProjectConfiguration","ACEClientAppTests/AcceptanceEvidenceContractTests/testSourceBoundaryInspection"]
args=["/Library/Frameworks/Python.framework/Versions/3.14/bin/python3",str(root/"tools/ace_ios_local.py"),"--evidence-root",str(ev/"digest-focused-runs"),"selected","--device","iPhone 17 Pro Max"]
for test in selectors:args.extend(["--test",test])
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
r=subprocess.run(args,cwd=root,capture_output=True,text=True)
(ev/"native-digest-focused-console.log").write_text(r.stdout+r.stderr)
record={"command":args,"startedUTC":start,"finishedUTC":datetime.datetime.now(datetime.timezone.utc).isoformat(),"runnerExit":r.returncode,"stdout":r.stdout,"stderr":r.stderr}
(ev/"native-digest-focused-command.json").write_text(json.dumps(record,indent=2))
print(json.dumps({k:v for k,v in record.items() if k!="command"}),flush=True)
raise SystemExit(r.returncode)
