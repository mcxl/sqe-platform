import importlib.util, json, os, sys, traceback
from pathlib import Path
os.umask(0o077)
root=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
spec=importlib.util.spec_from_file_location('ace_runner',root/'tools/ace_ios_local.py')
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
e=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914/settings-bold-integration')
e.mkdir(mode=0o700,exist_ok=False)
template=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914/derived-diagnostic/Build/Products/ACEClientAppUITests_iphonesimulator26.4-x86_64.xctestrun')
identifier='D1BAA05C-52DD-4E57-832F-C0A75718E085'
record={'question':'Does native Bold Text change match the app observation and restore to its original value?', 'candidate':module.candidate(allow_dirty=True),'templateSha256':module.sha256(template),'runnerSha256':module.sha256(root/'tools/ace_ios_local.py')}
before=None
try:
    before=module.native_flags(identifier,template,e,'before',{'mode':'read'})
    record['before']=before
    requested={**before,'boldText':not before['boldText']}
    record['changed']=module.native_flags(identifier,template,e,'changed',{'mode':'set',**requested})
except Exception as error:
    record['error']=str(error);record['traceback']=traceback.format_exc()
finally:
    if before is not None:
        try: record['restored']=module.native_flags(identifier,template,e,'restored',{'mode':'set',**before})
        except Exception as error: record['restoreError']=str(error)
    record['candidateAfter']=module.candidate(allow_dirty=True)
    record['passed']=('error' not in record and 'restoreError' not in record and record.get('restored')==before and record['candidateAfter']==record['candidate'])
    (e/'integration.json').write_text(json.dumps(record,indent=2,sort_keys=True))
    print(json.dumps({'passed':record['passed'],'error':record.get('error'),'restoreError':record.get('restoreError'),'evidence':str(e)},sort_keys=True))
sys.exit(0 if record['passed'] else 1)
