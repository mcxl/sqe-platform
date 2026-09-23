from pathlib import Path
import subprocess,json,datetime
root=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
ev=Path(__file__).parent
args=['/Library/Frameworks/Python.framework/Versions/3.14/bin/python3', 'LOCAL_HOME/Developer/sqe-platform-release-layout/tools/ace_ios_local.py', '--evidence-root', 'LOCAL_HOME/ace-private/mcx19b-complete-pilot-20260915/pilot-runs', 'pilot', '--pocock-evidence', 'LOCAL_HOME/ace-private/mcx19b-implementation-20260914/pilot-preparation-20260915/settings-navigation-fix/pocock-readiness-4646715.json', '--functional-evidence', 'LOCAL_HOME/ace-private/mcx19b-implementation-20260914/pilot-preparation-20260915/settings-navigation-fix/functional-readiness-4646715.json', '--evidence-gate', 'LOCAL_HOME/ace-private/mcx19b-implementation-20260914/pilot-preparation-20260915/settings-navigation-fix/evidence-gate-readiness-4646715.json', '--private-input-record', 'LOCAL_HOME/ace-private/mcx19b-implementation-20260914/pilot-preparation-20260915/settings-navigation-fix/private-input-readiness-4646715.json']
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
r=subprocess.run(args,cwd=root,capture_output=True,text=True)
(ev/"pilot-console.log").write_text(r.stdout+r.stderr)
record={"command":args,"startedUTC":start,"finishedUTC":datetime.datetime.now(datetime.timezone.utc).isoformat(),"runnerExit":r.returncode,"stdout":r.stdout,"stderr":r.stderr}
(ev/"pilot-command.json").write_text(json.dumps(record,indent=2)+"\n")
print(json.dumps({k:v for k,v in record.items() if k!="command"}),flush=True)
raise SystemExit(r.returncode)
