from pathlib import Path
import subprocess,json,hashlib,datetime
root=Path("LOCAL_HOME/ace-private/mcx19b-implementation-20260914/pilot-preparation-20260915/failure-probe-source")
ev=root.parent
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
args=["/Library/Frameworks/Python.framework/Versions/3.14/bin/python3",str(root/"tools/ace_ios_local.py"),"--evidence-root",str(ev/"failure-runs"),"selected","--diagnostic-dirty","--device","iPhone 17 Pro Max","--test","ACEClientAppTests/ACEClientAppTests/testRequestIsGETAndHasNoCache"]
r=subprocess.run(args,cwd=root,capture_output=True,text=True)
(ev/"native-gate-fail-console.log").write_text(r.stdout+r.stderr)
record={"command":args,"startedUTC":started,"finishedUTC":datetime.datetime.now(datetime.timezone.utc).isoformat(),"runnerExit":r.returncode,"stdout":r.stdout,"stderr":r.stderr}
(ev/"native-gate-fail-command.json").write_text(json.dumps(record,indent=2))
print(json.dumps(record),flush=True)
raise SystemExit(r.returncode)
