from pathlib import Path
import json,sys,importlib.util,datetime,subprocess,threading,time
repo=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
stage=Path('LOCAL_HOME/ace-private/mcx19b-release-timeout-20260915')
run=stage/'01-unchanged-prefix'
run.mkdir(mode=0o700,exist_ok=False)
spec=importlib.util.spec_from_file_location('ace_runner',repo/'tools/ace_ios_local.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
pre=json.loads((stage/'preflight.json').read_text());candidate=pre['candidate'];build=pre['retainedBuild'];template=Path(build['template'])
assert m.candidate()==candidate
assert m.sha256(template)==build['identity'] and m.directory_hash(Path(build['products']))==build['productSha256']
old=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914/pilot-preparation-20260915/settings-navigation-fix')
readiness=m.pilot_readiness(candidate,{'pocock':old/'pocock-readiness-4646715.json','functional':old/'functional-readiness-4646715.json','evidence-gate':old/'evidence-gate-readiness-4646715.json','private-input':old/'private-input-readiness-4646715.json'})
(run/'readiness-reuse.json').write_text(json.dumps(readiness,indent=2))
device,settings,allcases=m.coverage_batches(m.pilot_cases())[0]
cases=allcases[:2]
assert [c.scenario for c in cases]==['signIn','release']
identifier=pre['environment']['devices'][device]['udid']
initial=m.simulator_state(identifier);previous=None;flags=None
result={'startedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'question':'Does the unchanged failing batch prefix reproduce the release-final audit timeout?','candidate':candidate,'casePayloads':[c.payload() for c in cases],'originalBootState':initial,'retainedBuild':build,'correctionAttempt':False,'restorationFailures':[]}
stop=threading.Event()
def sample():
 while not stop.is_set():
  data={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
  for key,args in [('processes',['ps','-A','-o','pid,pcpu,pmem,etime,comm']),('thermal',['pmset','-g','therm']),('vm',['vm_stat'])]:
   try:
    p=subprocess.run(args,capture_output=True,text=True,timeout=15)
    data[key]=p.stdout if key!='processes' else '\n'.join(p.stdout.splitlines()[:1]+sorted(p.stdout.splitlines()[1:],key=lambda x:float(x.split()[1]),reverse=True)[:12])
   except Exception as e:data[key]=str(e)
  with (run/'resource-observations.jsonl').open('a') as f:f.write(json.dumps(data)+'\n')
  stop.wait(30)
thread=threading.Thread(target=sample,daemon=True);thread.start()
try:
 m.boot_required_simulator(identifier,initial)
 previous=m.current_simctl_settings(identifier)
 flags=m.native_flags(identifier,template,run,'read',{'mode':'read'})
 expected={'boldText':False,'reduceMotion':False,'increaseContrast':False,'orientation':'portrait'}
 assert flags==expected,flags
 result['originalSimctlSettings']=previous;result['originalNativeFlags']=flags
 (run/'starting-state.json').write_text(json.dumps(result,indent=2))
 result['batch']=m.run_batch(device,identifier,settings,cases,build,run,1)
 result['nativeResult']='passed'
except Exception as e:
 result['nativeResult']='failed';result['error']=str(e)
finally:
 if previous is not None:
  result['restorationFailures'].extend(m.restore_simctl_settings(identifier,previous,run,device))
  try:
   actual=m.current_simctl_settings(identifier);result['simctlReadback']=actual
   if actual!=previous:result['restorationFailures'].append('simctl-readback')
  except Exception as e:result['restorationFailures'].append(str(e))
 if flags is not None:
  try:
   actual=m.native_flags(identifier,template,run,'restore',{'mode':'set',**flags});result['nativeFlagReadback']=actual
   if actual!=flags:result['restorationFailures'].append('native-flags')
  except Exception as e:result['restorationFailures'].append(str(e))
 try:m.restore_boot_state(identifier,initial)
 except Exception as e:result['restorationFailures'].append(str(e))
 result['candidateUnchanged']=m.candidate()==candidate
 result['finishedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 stop.set();thread.join(timeout=45)
 (run/'result.json').write_text(json.dumps(result,indent=2))
print(json.dumps({'result':result['nativeResult'],'error':result.get('error'),'restorationFailures':result['restorationFailures'],'evidence':str(run)},indent=2))
sys.exit(0 if result['nativeResult']=='passed' and not result['restorationFailures'] and result['candidateUnchanged'] else 2)
