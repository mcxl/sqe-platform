from pathlib import Path
import importlib.util,sys,json,os,subprocess
from datetime import datetime,timezone
os.umask(0o077)
root=Path("LOCAL_HOME/Developer/sqe-platform-release-layout");stage=Path("LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915")
out=stage/"03-ax-startup-isolation";out.mkdir(mode=0o700)
spec=importlib.util.spec_from_file_location("ace",root/"tools/ace_ios_local.py");m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
c=json.loads((stage/"clean-candidate.json").read_text());assert m.candidate()==c
failed=stage/"pilot-runs/20260915T062647Z-pilot-d12f05a89420"
build=failed/"build";template=m.generated_xctestrun(build)
d17="2EB0863C-470E-467D-A0C6-CD216DA70C67";dmax="D1BAA05C-52DD-4E57-832F-C0A75718E085";other="3BF9AAA5-33AA-4EF3-BFEC-65C83DF5D79F"
record={"startedUTC":datetime.now(timezone.utc).isoformat(),"candidate":c,"status":"running","question":"Does the unchanged iPhone17 native settings-read test initialize after the idle approved ProMax simulator is shut down?","changedVariable":"ProMax simulator stopped during iPhone17 check; unrelated16ProMax untouched","initialStates":{i:m.simulator_state(i) for i in [d17,dmax,other]},"template":str(template),"templateSha256":m.sha256(template),"productsSha256":m.directory_hash(build/"Build/Products"),"restorationFailures":[],"pilotCasesExecuted":0}
def save(): (out/"result.json").write_text(json.dumps(record,indent=2))
def resources(): return {"atUTC":datetime.now(timezone.utc).isoformat(),"processes":subprocess.check_output(["ps","-axo","pid,ppid,pcpu,rss,state,comm"],text=True),"swap":subprocess.check_output(["sysctl","vm.swapusage"],text=True),"power":subprocess.check_output(["pmset","-g","therm"],text=True)}
assert record["initialStates"]=={d17:"Shutdown",dmax:"Booted",other:"Booted"}
record["beforeResources"]=resources();save()
try:
 record["shutdownProMax"]=m.checked(["xcrun","simctl","shutdown",dmax],timeout=120);save()
 m.boot_required_simulator(d17,"Shutdown")
 record["beforeTestResources"]=resources();save()
 record["observed"]=m.native_flags(d17,template,out,"unchanged-read",{"mode":"read"})
 record["status"]="passed; reduced simulator load diagnostic, not proof of AX cause"
except Exception as error:
 record["status"]="failed";record["error"]=str(error)
finally:
 try:m.restore_boot_state(d17,"Shutdown")
 except Exception as error:record["restorationFailures"].append("iPhone17: "+str(error))
 try:m.boot_required_simulator(dmax,"Shutdown")
 except Exception as error:record["restorationFailures"].append("ProMax: "+str(error))
 record["finalStates"]={i:m.simulator_state(i) for i in [d17,dmax,other]}
 if record["finalStates"]!=record["initialStates"]:record["restorationFailures"].append("boot state mismatch")
 record["afterResources"]=resources();record["candidateUnchanged"]=m.candidate()==c
 record["finishedUTC"]=datetime.now(timezone.utc).isoformat();save()
print(json.dumps({k:record.get(k) for k in ["status","observed","error","restorationFailures","candidateUnchanged","finishedUTC"]}))
sys.exit(0 if record["status"].startswith("passed") and not record["restorationFailures"] and record["candidateUnchanged"] else 2)
