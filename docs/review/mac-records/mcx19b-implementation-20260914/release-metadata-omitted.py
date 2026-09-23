from pathlib import Path
import importlib.util,sys,json,plistlib,time,traceback,os
os.umask(0o077)
base=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914');root=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
helper=root/'tools/ace_ios_local.py'
spec=importlib.util.spec_from_file_location('ace_runner',helper);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
e=base/'release-metadata-omitted';e.mkdir(mode=0o700,exist_ok=False)
control=base/'release-audit-sequence-pair';build=json.loads((control/'build-identity.json').read_text())
assert m.directory_hash(Path(build['products']))==build['productSha256']
identifier='D1BAA05C-52DD-4E57-832F-C0A75718E085';original=m.candidate();previous=m.current_simctl_settings(identifier)
record={'question':'Does the post-scroll unrestricted audit still fail when the existing phone-preview option omits the test-only metadata label?','singleVariable':'UITargetAppEnvironmentVariables.ACE_UI_TEST_SHOW_DIAGNOSTICS=0. Reuse the omit-initial comparison build and all other inputs.','controlEvidence':str(control/'omit-initial'),'expectedDiagnosticAssertions':['Appearance indicator must exist','The displayed view must use light appearance before the initial audit'],'nativeAuditExpectation':'Inspect all retained native audit findings separately. A metadata-assertion failure is expected and is not an acceptance pass.','candidate':original,'buildIdentity':build,'started':time.time(),'acceptedCoverageCases':0}
try:
 assert previous=={'appearance':'light','content_size':'large','increase_contrast':'disabled'}
 payload=plistlib.loads((control/'omit-initial/selected.xctestrun').read_bytes())
 payload['ACEClientAppUITests'].setdefault('UITargetAppEnvironmentVariables',{})['ACE_UI_TEST_SHOW_DIAGNOSTICS']='0'
 runfile=e/'selected.xctestrun';runfile.write_bytes(plistlib.dumps(payload))
 selector='ACEClientAppUITests/ACEClientAppUITests/testFictionalReleaseHasApprovedCopyControls';bundle=e/'result.xcresult'
 process=m.command(['xcodebuild','test-without-building','-xctestrun',str(runfile),'-destination','id='+identifier,'-parallel-testing-enabled','NO','-only-testing:'+selector,'-resultBundlePath',str(bundle)],cwd=root,timeout=900)
 (e/'command.json').write_text(json.dumps(process,indent=2));(e/'native.log').write_text(process.get('stdout','')+process.get('stderr',''))
 data=json.loads(m.checked(['xcrun','xcresulttool','get','test-results','summary','--path',str(bundle)],timeout=120)['stdout']);(e/'summary.json').write_text(json.dumps(data,indent=2))
 m._export_attachments(bundle,e/'attachments')
 assert data['totalTestCount']==1 and data['skippedTests']==0
 record.update(nativeExit=process['exit'],summary=str(e/'summary.json'),nativeIssues=m.marker_records(e/'native.log','ACE_A11Y_ISSUE '))
 record['productUnchanged']=m.directory_hash(Path(build['products']))==build['productSha256']
except Exception as error:record['error']=str(error);record['traceback']=traceback.format_exc()
finally:
 record['restorationErrors']=m.restore_simctl_settings(identifier,previous,e,'iPhone 17 Pro Max');record['candidateUnchanged']=m.candidate()==original;record['finished']=time.time();(e/'diagnostic.json').write_text(json.dumps(record,indent=2))
print(json.dumps({'nativeExit':record.get('nativeExit'),'nativeIssueCount':len(record.get('nativeIssues',[])),'error':record.get('error'),'evidence':str(e)}))
raise SystemExit(0 if 'nativeExit' in record and not record.get('error') and record.get('productUnchanged') and record['candidateUnchanged'] and not record['restorationErrors'] else 1)
