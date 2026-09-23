from pathlib import Path
import importlib.util,sys,json,os,time,traceback,hashlib
os.umask(0o077)
base=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914')
root=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
helper=base/'runner-b9ba714-diagnostic.py'
spec=importlib.util.spec_from_file_location('ace_runner',helper)
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
m.ROOT=root;m.IOS_ROOT=root/'ios/ACEClientApp';m.PROJECT=m.IOS_ROOT/'ACEClientApp.xcodeproj'
e=base/'release-current-build';e.mkdir(mode=0o700,exist_ok=False)
manifestPath=base/'ace-ios-local-runs/20260914T101054Z-selected-da6dcb775554/manifest.json'
manifest=json.loads(manifestPath.read_text());assert manifest['exit']==0
build=manifest['build'];template=Path(build['template'])
assert m.sha256(template)==build['identity'] and m.directory_hash(Path(build['products']))==build['productSha256']
sourceHashes={p:h for p,h in manifest['candidate']['sourceHashes'].items() if p.startswith('ios/')}
assert all(m.sha256(root/p)==h for p,h in sourceHashes.items())
identifier='D1BAA05C-52DD-4E57-832F-C0A75718E085'
record={'question':'Does the release Copy-control and post-scroll unrestricted audit check pass on the current unchanged iOS source?', 'started':time.time(),'sourceHashes':sourceHashes,'reviewCommit':'b9ba714d99862e9ef5572b7eb2a1b1d6471d0932','buildManifest':str(manifestPath),'executionHelper':str(helper),'executionHelperSha256':m.sha256(helper),'acceptedCoverageCases':0}
try:
 record['environment']=m.preflight();record['settings']=m.current_simctl_settings(identifier)
 assert record['settings']=={'appearance':'light','content_size':'large','increase_contrast':'disabled'}
 runfile=e/'selected.xctestrun';m.configure_xctestrun(template,runfile,{'ACE_UI_TEST_APPEARANCE':'light'})
 selector='ACEClientAppUITests/ACEClientAppUITests/testFictionalReleaseHasApprovedCopyControls'
 bundle=e/'result.xcresult'
 process=m.command(['xcodebuild','test-without-building','-xctestrun',str(runfile),'-destination','id='+identifier,'-parallel-testing-enabled','NO','-only-testing:'+selector,'-resultBundlePath',str(bundle)],cwd=m.IOS_ROOT,timeout=1800)
 (e/'command.json').write_text(json.dumps(process,indent=2));(e/'native.log').write_text(process.get('stdout','')+process.get('stderr',''))
 record['exit']=process['exit'];record['selector']=selector
 errors=[]
 try:m.native_summary(bundle,e/'summary.json',1)
 except Exception as error:errors.append(str(error))
 try:m._export_attachments(bundle,e/'attachments')
 except Exception as error:errors.append(str(error))
 record['collectionErrors']=errors
 record['nativePassed']=process['exit']==0 and not errors
except Exception as error:record['error']=str(error);record['traceback']=traceback.format_exc()
record['sourceUnchanged']=all(m.sha256(root/p)==h for p,h in sourceHashes.items())
record['finished']=time.time();(e/'diagnostic.json').write_text(json.dumps(record,indent=2,sort_keys=True))
print(json.dumps({'nativePassed':record.get('nativePassed'),'exit':record.get('exit'),'error':record.get('error'),'evidence':str(e)}))
raise SystemExit(0 if record.get('nativePassed') and record['sourceUnchanged'] else 1)
