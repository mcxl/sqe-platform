from pathlib import Path
import subprocess,json,datetime,hashlib
root=Path("LOCAL_HOME/Developer/sqe-platform-release-layout")
ev=Path(__file__).parent
previous=json.loads((ev.parent/"native-functional-final-command.json").read_text())
args=previous["command"][:]
args[args.index("--evidence-root")+1]=str(ev/"functional-runs")
assert subprocess.run(["git","status","--porcelain"],cwd=root,capture_output=True,text=True,check=True).stdout==""
assert json.loads((ev/"result.json").read_text())["passed"] is True
assert hashlib.sha256((root/"ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift").read_bytes()).hexdigest()=="b91ff4bc1501fa9cdb0de4cd2d4f4b6f8c4370b98c09ca613f2c5e729922353f"
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
r=subprocess.run(args,cwd=root,capture_output=True,text=True)
(ev/"functional-console.log").write_text(r.stdout+r.stderr)
record={"command":args,"startedUTC":start,"finishedUTC":datetime.datetime.now(datetime.timezone.utc).isoformat(),"runnerExit":r.returncode,"stdout":r.stdout,"stderr":r.stderr}
(ev/"functional-command.json").write_text(json.dumps(record,indent=2)+"\n")
print(json.dumps({k:v for k,v in record.items() if k!="command"}),flush=True)
raise SystemExit(r.returncode)
