from pathlib import Path
import importlib.util,sys,json,os,time,traceback
os.umask(0o077)
base=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914')
root=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
spec=importlib.util.spec_from_file_location('ace_runner',root/'tools/ace_ios_local.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
e=base/'functional-after-literal-correction';e.mkdir(mode=0o700,exist_ok=False)
passedPath=base/'ace-ios-local-runs/20260914T100656Z-selected-6532f26731b7/manifest.json'
passed=json.loads(passedPath.read_text());build=passed['build'];candidate=m.candidate(allow_dirty=True)
assert candidate==passed['candidate']==build['candidate']
assert build['scheme']=='ACEClientApp'
template=Path(build['template']);assert m.sha256(template)==build['identity']
assert m.directory_hash(Path(build['products']))==build['productSha256']
identifier='D1BAA05C-52DD-4E57-832F-C0A75718E085'
selectors=m.enumerate_selectors(template,identifier,e)
assert len(selectors)==66,len(selectors)
contract=[s for s in selectors if '/AcceptanceEvidenceContractTests/' in s]
assert len(contract)==43,len(contract)
record={'started':time.time(),'candidate':candidate,'buildManifest':str(passedPath),'buildManifestSha256':m.sha256(passedPath),'selectors':sorted(selectors),'inventoryTotal':66,'includedContractTests':43,'environment':m.preflight(),'scope':'Unit and contract checks; pending-record checks do not prove runtime behaviour'}
runfile=e/'current.xctestrun';m.configure_xctestrun(template,runfile,{},'ACEClientAppTests')
bundle=e/'result.xcresult'
try:
    process=m.command(['xcodebuild','test-without-building','-xctestrun',str(runfile),'-destination','id='+identifier,'-parallel-testing-enabled','NO','-resultBundlePath',str(bundle)],cwd=m.IOS_ROOT,timeout=1800)
    record['command']=process
    (e/'native.log').write_text(str(process['stdout'])+str(process['stderr']))
    count=m.native_summary(bundle,e/'summary.json',66)
    assert process['exit']==0,process['exit']
    assert count==66,count
    record['resultBundleSha256']=m.directory_hash(bundle)
    record['nativeTestCount']=count
except Exception as error:
    record['error']=str(error);record['traceback']=traceback.format_exc()
finally:
    if bundle.is_dir():
        tree=m.command(['xcrun','xcresulttool','get','test-results','tests','--path',str(bundle),'--compact'],timeout=60)
        (e/'tests.json').write_text(str(tree['stdout']))
        try:m._export_attachments(bundle,e/'attachments')
        except Exception as error:record['attachmentError']=str(error)
    record['candidateAfter']=m.candidate(allow_dirty=True)
    record['passed']='error' not in record and record['candidateAfter']==candidate
    record['finished']=time.time()
    (e/'functional-evidence.json').write_text(json.dumps(record,indent=2,sort_keys=True))
    print(json.dumps({'passed':record['passed'],'error':record.get('error'),'count':record.get('nativeTestCount'),'evidence':str(e)},sort_keys=True))
raise SystemExit(0 if record['passed'] else 1)
