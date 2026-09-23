from pathlib import Path
import subprocess,json,datetime,hashlib
root=Path("LOCAL_HOME/Developer/sqe-platform-release-layout")
ev=Path(__file__).parent
previous=json.loads((ev.parent/"native-functional-final-command.json").read_text())
args=previous["command"][:]
args[args.index("--evidence-root")+1]=str(ev/"functional-runs")
assert subprocess.run(["git","status","--porcelain"],cwd=root,capture_output=True,text=True,check=True).stdout==""
assert json.loads((ev/"result.json").read_text())["passed"] is True
assert hashlib.sha256((root/"ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift").read_bytes()).hexdigest()=="cccd23735441a3a3943f4b43581a9b597984a8d70fa89ec7b2ce026d239d7615"
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
r=subprocess.run(args,cwd=root,capture_output=True,text=True)
(ev/"functional-console.log").write_text(r.stdout+r.stderr)
record={"command":args,"startedUTC":start,"finishedUTC":datetime.datetime.now(datetime.timezone.utc).isoformat(),"runnerExit":r.returncode,"stdout":r.stdout,"stderr":r.stderr}
(ev/"functional-command.json").write_text(json.dumps(record,indent=2)+"\n")
print(json.dumps({k:v for k,v in record.items() if k!="command"}),flush=True)
raise SystemExit(r.returncode)
