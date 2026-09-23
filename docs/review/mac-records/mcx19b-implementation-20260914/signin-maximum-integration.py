from pathlib import Path
import importlib.util,sys,json,os,time,traceback
os.umask(0o077)
base=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914')
root=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
spec=importlib.util.spec_from_file_location('ace_runner',root/'tools/ace_ios_local.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
e=base/'signin-maximum-integration';e.mkdir(mode=0o700,exist_ok=False)
manifestPath=base/'ace-ios-local-runs/20260914T101054Z-selected-da6dcb775554/manifest.json'
manifest=json.loads(manifestPath.read_text());assert manifest['exit']==0
build=manifest['build'];template=Path(build['template'])
assert m.sha256(template)==build['identity'] and m.directory_hash(Path(build['products']))==build['productSha256']
assert m.candidate(allow_dirty=True)==manifest['candidate']
identifier='D1BAA05C-52DD-4E57-832F-C0A75718E085'
record={'question':'Do the corrected sign-in prompts remain visible and pass unrestricted native audits at maximum system text size in light and dark appearance?', 'started':time.time(),'candidate':manifest['candidate'],'buildManifest':str(manifestPath),'acceptedCoverageCases':0,'batches':[]}
before=None;simctlBefore=None
try:
 record['environment']=m.preflight();simctlBefore=m.current_simctl_settings(identifier);record['simctlBefore']=simctlBefore
 before=m.native_flags(identifier,template,e,'before',{'mode':'read'});record['flagsBefore']=before
 target={'boldText':False,'reduceMotion':False,'increaseContrast':False,'orientation':'portrait'}
 if before!=target:record['set']=m.native_flags(identifier,template,e,'set',{'mode':'set',**target})
 for index,appearance in enumerate(['light','dark']):
  settings=m.Settings(appearance,'accessibility-extra-extra-extra-large','portrait')
  case=m.make_case('diagnostic-signin-maximum','iPhone 17 Pro Max','signIn',settings,True)
  record['batches'].append(m.run_batch('iPhone 17 Pro Max',identifier,settings,(case,),{'template':str(template)},e,index))
except Exception as error:record['error']=str(error);record['traceback']=traceback.format_exc()
finally:
 try:
  if simctlBefore:
   for setting,value in simctlBefore.items():m.checked(['xcrun','simctl','ui',identifier,setting,value],timeout=60)
  if before:record['restored']=m.native_flags(identifier,template,e,'restored',{'mode':'set',**before})
 except Exception as error:record['restoreError']=str(error)
 record['simctlAfter']=m.current_simctl_settings(identifier);record['candidateAfter']=m.candidate(allow_dirty=True)
 record['passed']='error' not in record and 'restoreError' not in record and record.get('restored')==before and record['simctlAfter']==simctlBefore and record['candidateAfter']==record['candidate']
 record['finished']=time.time();(e/'integration.json').write_text(json.dumps(record,indent=2,sort_keys=True));print(json.dumps({'passed':record['passed'],'error':record.get('error'),'evidence':str(e)}))
raise SystemExit(0 if record['passed'] else 1)
