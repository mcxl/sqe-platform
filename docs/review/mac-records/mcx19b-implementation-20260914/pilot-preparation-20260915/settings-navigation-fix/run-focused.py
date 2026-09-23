from pathlib import Path
import importlib.util,sys,json,datetime,traceback
root=Path("LOCAL_HOME/Developer/sqe-platform-release-layout")
ev=Path(__file__).parent
spec=importlib.util.spec_from_file_location("ace_local",root/"tools/ace_ios_local.py")
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
def save(name,data):
 (ev/name).write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
def phase(name):
 print(name,flush=True);save("phase.json",{"phase":name,"utc":datetime.datetime.now(datetime.timezone.utc).isoformat()})
identifier="2EB0863C-470E-467D-A0C6-CD216DA70C67"
original={"mode":"set","boldText":False,"reduceMotion":False,"increaseContrast":False,"orientation":"portrait"}
result={"startedUTC":datetime.datetime.now(datetime.timezone.utc).isoformat(),"scope":"Settings observation diagnostic only; no formal coverage cases"}
build_record=None;booted=False;original_simctl=None;boot_state=None
try:
 phase("preflight")
 result["candidate"]=m.candidate(allow_dirty=True)
 assert result["candidate"]["commit"]=="b2c45093a44c6171ca250b858378ea57693d8477"
 result["environment"]=m.preflight();save("preflight.json",result)
 phase("generic build")
 build_record=m.build(result["candidate"],ev);save("build-record.json",build_record)
 assert m.candidate(allow_dirty=True)==result["candidate"]
 boot_state=m.simulator_state(identifier);result["initialBootState"]=boot_state
 m.boot_required_simulator(identifier,boot_state);booted=True
 original_simctl=m.current_simctl_settings(identifier);result["initialSimctl"]=original_simctl
 phase("recover original native settings")
 result["recovered"]=m.native_flags(identifier,Path(build_record["template"]),ev,"001-recover",original)
 phase("set all three native flags and landscape")
 requested={"mode":"set","boldText":True,"reduceMotion":True,"increaseContrast":True,"orientation":"landscape"}
 result["enabled"]=m.native_flags(identifier,Path(build_record["template"]),ev,"002-enable",requested)
 result["mainResult"]="passed"
except Exception as error:
 result["mainResult"]="failed";result["error"]=str(error);result["traceback"]=traceback.format_exc()
finally:
 if booted and build_record:
  phase("restore original native settings")
  try:result["restored"]=m.native_flags(identifier,Path(build_record["template"]),ev,"003-restore",original)
  except Exception as error:result["restorationError"]=str(error)
  if original_simctl:
   try:
    result["simctlRestorationFailures"]=m.restore_simctl_settings(identifier,original_simctl,ev,"iPhone 17")
    result["finalSimctl"]=m.current_simctl_settings(identifier)
    assert result["finalSimctl"]==original_simctl
   except Exception as error:result["simctlError"]=str(error)
  try:
   m.restore_boot_state(identifier,boot_state)
   result["finalBootState"]=m.simulator_state(identifier)
   assert result["finalBootState"]==boot_state
  except Exception as error:result["bootStateError"]=str(error)
 try:result["candidateUnchanged"]=m.candidate(allow_dirty=True)==result["candidate"]
 except Exception as error:result["candidateError"]=str(error)
 result["finishedUTC"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
 result["passed"]=result.get("mainResult")=="passed" and result.get("restored")=={k:v for k,v in original.items() if k!="mode"} and not any(k in result for k in ["restorationError","simctlError","bootStateError","candidateError"]) and result.get("candidateUnchanged")==True and not result.get("simctlRestorationFailures")
 save("result.json",result)
 phase("complete: "+str(result["passed"]))
 print(json.dumps({k:v for k,v in result.items() if k not in ["candidate","environment","traceback"]}),flush=True)
raise SystemExit(0 if result["passed"] else 2)
