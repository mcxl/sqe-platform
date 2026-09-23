from pathlib import Path
import json,sys,importlib.util,datetime,subprocess
repo=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
stage=Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915')
run=stage/'01-low-power-off-unchanged';run.mkdir(mode=0o700,exist_ok=False)
sp=importlib.util.spec_from_file_location('ace_runner',repo/'tools/ace_ios_local.py');m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m)
pre=json.loads((stage/'preflight.json').read_text());candidate=pre['candidate'];build=pre['retainedBuild'];template=Path(build['template'])
assert m.candidate()==candidate
assert m.sha256(template)==build['identity'] and m.directory_hash(Path(build['products']))==build['productSha256']
identifier=pre['environment']['devices']['iPhone 17']['udid'];initial=m.simulator_state(identifier)
request={'mode':'set','boldText':False,'reduceMotion':False,'increaseContrast':False,'orientation':'portrait'}
result={'startedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'question':'Does the unchanged failed orientation settings check pass with Low Power Mode off?','scope':'One selected settings test, plus original-state read and restoration checks. No coverage cases or audits.','candidate':candidate,'retainedBuild':build,'request':request,'initialBootState':initial,'restorationFailures':[],'correctionAttempt':False,'nativeResult':'pending','powerBefore':subprocess.check_output(['pmset','-g','custom'],text=True),'thermalBefore':subprocess.check_output(['pmset','-g','therm'],text=True)}
(run/'starting-state.json').write_text(json.dumps(result,indent=2));flags=None;settings=None
try:
 m.boot_required_simulator(identifier,initial)
 settings=m.current_simctl_settings(identifier)
 flags=m.native_flags(identifier,template,run,'read',{'mode':'read'})
 assert flags=={k:v for k,v in request.items() if k!='mode'},flags
 result['initialNativeFlags']=flags;result['initialSimctlSettings']=settings
 result['observed']=m.native_flags(identifier,template,run,'target',request)
 result['nativeResult']='passed'
except Exception as e:
 result['nativeResult']='failed';result['error']=str(e)
finally:
 if settings is not None:
  result['restorationFailures'].extend(m.restore_simctl_settings(identifier,settings,run,'iPhone 17'))
  try:
   result['simctlReadback']=m.current_simctl_settings(identifier)
   if result['simctlReadback']!=settings:result['restorationFailures'].append('simctl readback mismatch')
  except Exception as e:result['restorationFailures'].append(str(e))
 if flags is not None:
  try:
   result['restoredNativeFlags']=m.native_flags(identifier,template,run,'restore',{'mode':'set',**flags})
   if result['restoredNativeFlags']!=flags:result['restorationFailures'].append('native flag mismatch')
  except Exception as e:result['restorationFailures'].append(str(e))
 try:m.restore_boot_state(identifier,initial)
 except Exception as e:result['restorationFailures'].append(str(e))
 result['candidateUnchanged']=m.candidate()==candidate
 result['finalBootState']=m.simulator_state(identifier)
 result['finishedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 result['thermalAfter']=subprocess.check_output(['pmset','-g','therm'],text=True)
 (run/'result.json').write_text(json.dumps(result,indent=2))
print(json.dumps({'result':result['nativeResult'],'error':result.get('error'),'restorationFailures':result['restorationFailures'],'evidence':str(run)}))
sys.exit(0 if result['nativeResult']=='passed' and not result['restorationFailures'] and result['candidateUnchanged'] else 2)
