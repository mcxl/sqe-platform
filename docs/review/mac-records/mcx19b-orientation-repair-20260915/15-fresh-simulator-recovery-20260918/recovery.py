from pathlib import Path
import importlib.util,sys,json,datetime as dt,subprocess,plistlib,traceback
OLD=Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915/14-copy-reflow-check-20260917')
ROOT=Path(__file__).parent
spec=importlib.util.spec_from_file_location('d2_reuse',OLD/'d2_execution.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
DEADLINE=dt.datetime(2026,9,17,14,23,27,tzinfo=dt.timezone.utc)
def remaining():return int((DEADLINE-dt.datetime.now(dt.timezone.utc)).total_seconds())
rec={'approval':'free space available proceed','scope':'One fresh simulator recovery; one native invocation; no rebuild or retry','startedUTC':m.now(),'deadlineUTC':DEADLINE.isoformat(),'status':'preflight','mechanicalGateSuccess':False}
def save():m.write_json(ROOT/'recovery.json',rec)
def stage(s):rec['status']=s;save();print(s,flush=True)
def checked(cmd,timeout=60):
 r=m.run_command(cmd,timeout=min(timeout,max(1,remaining()-120)));rec.setdefault('setupCommands',[]).append(r);save()
 if r.get('exit')!=0 or r.get('timedOut'):raise RuntimeError(str(r))
 return r.get('output','').strip()
initial={};original={};target=None
try:
 if (ROOT/'invocation-started.json').exists():raise RuntimeError('Invocation already exists; no retry')
 assert remaining()>300,'Too little recovery time remains'
 assert not subprocess.run(['pgrep','-x','xcodebuild'],capture_output=True,text=True).stdout.strip(),'Existing xcodebuild'
 br=m.read_json(OLD/'build-record.json');runner=m.load_runner(br);rec['build']=m.check_build(OLD/'build-record.json',runner)
 initial=m.devices();rec['existingBootStates']=dict(initial)
 target=checked(['xcrun','simctl','create','ACE D2 Recovery 20260918','com.apple.CoreSimulator.SimDeviceType.iPhone-17','com.apple.CoreSimulator.SimRuntime.iOS-26-4'])
 rec['target']=target;initial[target]='Shutdown';save()
 checked(['xcrun','simctl','boot',target],120);checked(['xcrun','simctl','bootstatus',target,'-b'],240)
 original={k:m.setting(target,k) for k in ('appearance','content_size','increase_contrast')};rec['originalSettings']=original;save()
 expected={'appearance':'light','content_size':'large','increase_contrast':'disabled'}
 for k,v in expected.items():
  if original[k]!=v:checked(['xcrun','simctl','ui',target,k,v])
 rec['testSettings']={k:m.setting(target,k) for k in expected};assert rec['testSettings']==expected
 env={'ACE_D2_ARM':'Y','ACE_D2_MAX_CALLS':'2','ACE_D2_FORCE_FAIL':'1'}
 runfile=ROOT/'ACEClientAppUITests.xctestrun';runner.configure_xctestrun(Path(br['template']),runfile,env)
 actual=plistlib.loads(runfile.read_bytes())['ACEClientAppUITests']['EnvironmentVariables']
 assert all(actual.get(k)==v for k,v in env.items())
 rec['xctestrun']={'sha256':m.sha256(runfile),'environment':env}
 bundle=ROOT/'result.xcresult';cmd=['xcodebuild','test-without-building','-xctestrun',str(runfile),'-destination','id='+target,'-parallel-testing-enabled','NO','-only-testing:'+m.SELECTOR,'-resultBundlePath',str(bundle)]
 assert remaining()>240,'Insufficient time for native invocation and restoration'
 m.write_json(ROOT/'invocation-started.json',{'command':cmd,'time':m.now()});stage('native test running')
 rec['native']=m.run_command(cmd,ROOT/'native.log',timeout=min(720,remaining()-180));save()
 rec['calls'],rec['rawMarkerLines']=m.json_markers(ROOT/'native.log');rec['callCount']=len(rec['calls']);save()
 stage('retaining evidence')
 rec['exports']={}
 for kind in ('summary','tests'):
  result,text=m.run_capture(['xcrun','xcresulttool','get','test-results',kind,'--path',str(bundle)],timeout=min(45,max(1,remaining()-75)))
  rec['exports'][kind]=result
  try:payload=json.loads(text)
  except Exception:payload={'raw':text}
  m.write_json(ROOT/('native-'+kind+'.json'),payload);rec[kind]=payload
 export,text=m.run_capture(['xcrun','xcresulttool','export','attachments','--path',str(bundle),'--output-path',str(ROOT/'attachments')],timeout=min(45,max(1,remaining()-60)))
 rec['exports']['attachments']=export
 (ROOT/'attachments-export.log').write_text(text)
 rec['failures']=m._failure_texts(rec.get('summary',{}))
 rec['status']='native execution finished; review pending'
except BaseException as e:
 rec['error']=str(e);rec['traceback']=traceback.format_exc();rec['status']='stopped'
finally:
 save()
 if target:
  try:m.restore(target,initial,original,rec)
  except BaseException as e:rec['restorationError']=str(e)
 rec['finishedUTC']=m.now();save()
 print(json.dumps({k:rec.get(k) for k in ['status','target','native','callCount','failures','error','restoration','finishedUTC']}),flush=True)
