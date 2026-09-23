from pathlib import Path
import importlib.util,sys,json,os,subprocess
from datetime import datetime,timezone
os.umask(0o077)
root=Path("LOCAL_HOME/Developer/sqe-platform-release-layout")
stage=Path("LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915")
spec=importlib.util.spec_from_file_location("ace",root/"tools/ace_ios_local.py")
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
c=json.loads((stage/"clean-candidate.json").read_text());assert m.candidate()==c
paths={role:stage/(role+"-readiness.json") for role in m.READINESS_ROLES}
m.pilot_readiness(c,paths)
power=subprocess.check_output(["pmset","-g","custom"],text=True)
assert all(line.split()[-1]=="0" for line in power.splitlines() if "lowpowermode" in line)
record={"startedUTC":datetime.now(timezone.utc).isoformat(),"candidate":c,"lowPowerSettings":power,"status":"running","scope":"22 cases, 20 audit cases, 2 layout-only cases, 36 audit invocations"}
(stage/"pilot-execution.json").write_text(json.dumps(record,indent=2))
args=["--evidence-root",str(stage/"pilot-runs"),"pilot","--pocock-evidence",str(paths["pocock"]),"--functional-evidence",str(paths["functional"]),"--evidence-gate",str(paths["evidence-gate"]),"--private-input-record",str(paths["private-input"])]
code=m.main(args)
record.update({"finishedUTC":datetime.now(timezone.utc).isoformat(),"exit":code,"status":"native passed; inspection pending" if code==0 else "failed; evidence retained","candidateUnchanged":m.candidate()==c})
(stage/"pilot-execution.json").write_text(json.dumps(record,indent=2))
sys.exit(code)
