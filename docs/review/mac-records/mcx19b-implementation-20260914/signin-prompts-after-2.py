from pathlib import Path
import importlib.util,sys,json,os,time,traceback
os.umask(0o077)
base=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914')
root=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
spec=importlib.util.spec_from_file_location('ace_runner',root/'tools/ace_ios_local.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
e=base/'signin-prompts-after-2'; e.mkdir(mode=0o700,exist_ok=False)
template=base/'derived-diagnostic/Build/Products/ACEClientAppUITests_iphonesimulator26.4-x86_64.xctestrun'
inputs=json.loads((base/'signin-prompt-build-2-inputs.json').read_text())
for name,expected in inputs.items():
    assert m.sha256(root/name)==expected,name
identifier='D1BAA05C-52DD-4E57-832F-C0A75718E085'
settings=m.Settings('light','large','portrait')
case=m.make_case('diagnostic-integration','iPhone 17 Pro Max','signIn',settings,True)
record={'question':'Do both appearances retain readable sign-in prompts, secure password entry and a full native audit after the demonstrated colour correction?','started':time.time(),'candidate':m.candidate(allow_dirty=True),'buildInputs':inputs,'templateSha256':m.sha256(template),'productSha256':m.directory_hash(template.parent),'buildEvidence':str(base/'signin-prompt-build-2.xcresult'),'acceptedCoverageCases':0}
before=None;simctlBefore=None
try:
    record['environment']=m.preflight()
    simctlBefore=m.current_simctl_settings(identifier);record['simctlBefore']=simctlBefore
    before=m.native_flags(identifier,template,e,'before',{'mode':'read'});record['flagsBefore']=before
    target={'boldText':False,'reduceMotion':False,'increaseContrast':False,'orientation':'portrait'}
    if before!=target:record['set']=m.native_flags(identifier,template,e,'set',{'mode':'set',**target})
    record['batches']=[]
    for index,appearance in enumerate(['light','dark']):
        settings=m.Settings(appearance,'large','portrait')
        case=m.make_case('diagnostic-prompt-correction','iPhone 17 Pro Max','signIn',settings,True)
        record['batches'].append(m.run_batch('iPhone 17 Pro Max',identifier,settings,(case,),{'template':str(template)},e,index))
except Exception as error:
    record['error']=str(error);record['traceback']=traceback.format_exc()
finally:
    try:
        if simctlBefore:
            for setting,value in simctlBefore.items():m.checked(['xcrun','simctl','ui',identifier,setting,value],timeout=60)
        if before:record['restored']=m.native_flags(identifier,template,e,'restored',{'mode':'set',**before})
    except Exception as error:record['restoreError']=str(error)
    record['simctlAfter']=m.current_simctl_settings(identifier)
    record['candidateAfter']=m.candidate(allow_dirty=True)
    record['passed']=('error' not in record and 'restoreError' not in record and record.get('restored')==before and record['simctlAfter']==simctlBefore and record['candidateAfter']==record['candidate'])
    record['finished']=time.time()
    (e/'integration.json').write_text(json.dumps(record,indent=2,sort_keys=True))
    print(json.dumps({'passed':record['passed'],'error':record.get('error'),'restoreError':record.get('restoreError'),'evidence':str(e)},sort_keys=True))
raise SystemExit(0 if record['passed'] else 1)
