from pathlib import Path
import json,sys,importlib.util,datetime,subprocess
stage=Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915');run=stage/'02-native-orientation-proof';run.mkdir(mode=0o700,exist_ok=False)
repo=Path('LOCAL_HOME/Developer/sqe-platform-release-layout');probe=stage/'negative-probe-worktree'
def load(root,name):
 sp=importlib.util.spec_from_file_location(name,root/'tools/ace_ios_local.py');v=importlib.util.module_from_spec(sp);sys.modules[name]=v;sp.loader.exec_module(v);return v
m=load(repo,'fixed_runner');n=load(probe,'negative_runner')
result={'startedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'running','question':'Does the repaired helper reject a measured wrong orientation and accept correct portrait and landscape without an outer cancelling waiter?','candidate':m.candidate(allow_dirty=True),'negativeCandidate':n.candidate(allow_dirty=True),'restorationFailures':[],'checks':{},'pilotCasesExecuted':0}
def save(phase):
 result['phase']=phase;(run/'progress.json').write_text(json.dumps(result,indent=2));print(json.dumps({'phase':phase,'evidence':str(run)}),flush=True)
def frame_for(label,requested,outcome):
 root=run/'native-settings'/label;records=m.marker_records(root/'native.log','ACE_ORIENTATION_FRAME');assert len(records)==1,records
 f=records[0];assert f['requested']==requested and f['outcome']==outcome,f
 width,height=float(f['frame']['width']),float(f['frame']['height']);assert width>0 and height>0
 assert (width>height)==(requested=='landscape') if outcome=='match' else (height>width and requested=='landscape')
 return f
identifier='2EB0863C-470E-467D-A0C6-CD216DA70C67';initial=None;flags=None;settings=None;fixed_build=None
try:
 result['environment']=m.preflight();save('building corrected test')
 fixed_root=run/'fixed-build';fixed_root.mkdir();fixed_build=m.build(result['candidate'],fixed_root);result['fixedBuild']=fixed_build
 save('building deliberate mismatch control')
 negative_root=run/'negative-build';negative_root.mkdir();negative_build=n.build(result['negativeCandidate'],negative_root);result['negativeBuild']=negative_build
 assert m.candidate(allow_dirty=True)==result['candidate'];assert n.candidate(allow_dirty=True)==result['negativeCandidate']
 initial=m.simulator_state(identifier);result['initialBootState']=initial;m.boot_required_simulator(identifier,initial)
 settings=m.current_simctl_settings(identifier);flags=m.native_flags(identifier,Path(fixed_build['template']),run,'read',{'mode':'read'})
 result['initialSimctlSettings']=settings;result['initialNativeFlags']=flags
 assert flags=={'boldText':False,'reduceMotion':False,'increaseContrast':False,'orientation':'portrait'},flags
 request={'mode':'set','boldText':False,'reduceMotion':False,'increaseContrast':False,'orientation':'portrait'}
 save('running deliberate mismatch; expected native failure')
 negative_error=None
 try:m.native_flags(identifier,Path(negative_build['template']),run,'negative-portrait',request)
 except Exception as e:negative_error=str(e)
 root=run/'native-settings/negative-portrait';c=json.loads((root/'command.json').read_text());s=json.loads((root/'summary.json').read_text())
 assert c['exit']==65 and s['totalTestCount']==1 and s['failedTests']==1 and s['skippedTests']==0 and s['passedTests']==0,(c['exit'],s)
 assert len(s['testFailures'])==1 and 'Native app frame does not match requested landscape orientation' in s['testFailures'][0]['failureText'],s
 result['checks']['deliberateMismatch']={'status':'expected failure verified','nativeExit':65,'nativeSummary':s,'frame':frame_for('negative-portrait','landscape','mismatch'),'collectorError':negative_error}
 save('running corrected portrait; expected pass')
 actual=m.native_flags(identifier,Path(fixed_build['template']),run,'corrected-portrait',request)
 result['checks']['portrait']={'status':'passed','observed':actual,'frame':frame_for('corrected-portrait','portrait','match')}
 save('running corrected landscape; expected pass')
 actual=m.native_flags(identifier,Path(fixed_build['template']),run,'corrected-landscape',{**request,'orientation':'landscape'})
 result['checks']['landscape']={'status':'passed','observed':actual,'frame':frame_for('corrected-landscape','landscape','match')}
 result['status']='passed'
except Exception as e:
 result['status']='failed';result['error']=str(e)
finally:
 save('restoring original simulator state')
 if settings is not None:
  result['restorationFailures'].extend(m.restore_simctl_settings(identifier,settings,run,'iPhone 17'))
  try:
   result['simctlReadback']=m.current_simctl_settings(identifier)
   if result['simctlReadback']!=settings:result['restorationFailures'].append('simctl readback mismatch')
  except Exception as e:result['restorationFailures'].append(str(e))
 if flags is not None and fixed_build is not None:
  try:
   actual=m.native_flags(identifier,Path(fixed_build['template']),run,'restore',{'mode':'set',**flags});result['restoredNativeFlags']=actual
   if actual!=flags:result['restorationFailures'].append('native flag mismatch')
  except Exception as e:result['restorationFailures'].append(str(e))
 if initial is not None:
  try:m.restore_boot_state(identifier,initial)
  except Exception as e:result['restorationFailures'].append(str(e))
 result['candidateUnchanged']=m.candidate(allow_dirty=True)==result['candidate'];result['finishedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 if result['restorationFailures'] or not result['candidateUnchanged']:result['status']='failed'
 (run/'result.json').write_text(json.dumps(result,indent=2));save('complete')
print(json.dumps({'result':result['status'],'error':result.get('error'),'restorationFailures':result['restorationFailures'],'evidence':str(run)}),flush=True)
sys.exit(0 if result['status']=='passed' else 2)
