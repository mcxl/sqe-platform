from pathlib import Path
import importlib.util,sys,json,time,traceback,os
os.umask(0o077)
base=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914')
e=base/'native-copy-paste-probe-2'
root=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
helper=root/'tools/ace_ios_local.py'
spec=importlib.util.spec_from_file_location('ace_runner',helper);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
record={'question':json.loads((e/'source-provenance.json').read_text())['question'],'started':time.time(),'runs':[],'helperSha256':m.sha256(helper),'acceptedCoverageCases':0}
identifier='D1BAA05C-52DD-4E57-832F-C0A75718E085'
original=m.candidate();previous=m.current_simctl_settings(identifier)
assert previous=={'appearance':'light','content_size':'large','increase_contrast':'disabled'}
record['sourceCandidate']=original;record['settingsBefore']=previous
try:
 record['environment']=m.preflight()
 m.ROOT=e/'source';m.IOS_ROOT=m.ROOT/'ios/ACEClientApp';m.PROJECT=m.IOS_ROOT/'ACEClientApp.xcodeproj'
 build=m.build(json.loads((e/'source-provenance.json').read_text()),e)
 (e/'build-identity.json').write_text(json.dumps(build,indent=2))
 for name,skip in [('copy-paste','0')]:
  run=e/name;run.mkdir()
  runfile=run/'selected.xctestrun';m.configure_xctestrun(Path(build['template']),runfile,{'ACE_UI_TEST_APPEARANCE':'light','ACE_NATIVE_COPY_PROBE':'1'})
  selector='ACEClientAppUITests/ACEClientAppUITests/testNativeCopyPasteProbe'
  bundle=run/'result.xcresult'
  process=m.command(['xcodebuild','test-without-building','-xctestrun',str(runfile),'-destination','id='+identifier,'-parallel-testing-enabled','NO','-only-testing:'+selector,'-resultBundlePath',str(bundle)],cwd=m.IOS_ROOT,timeout=900)
  (run/'command.json').write_text(json.dumps(process,indent=2));(run/'native.log').write_text(process.get('stdout','')+process.get('stderr',''))
  summary=m.checked(['xcrun','xcresulttool','get','test-results','summary','--path',str(bundle)],timeout=120)
  data=json.loads(summary['stdout']);(run/'summary.json').write_text(json.dumps(data,indent=2))
  m._export_attachments(bundle,run/'attachments')
  assert data['totalTestCount']==1 and data['skippedTests']==0 and data['expectedFailures']==0
  row={'name':name,'skipInitial':skip=='1','nativeExit':process['exit'],'summary':str(run/'summary.json'),'failedTests':data['failedTests'],'passedTests':data['passedTests'],'issues':m.marker_records(run/'native.log','ACE_A11Y_ISSUE '),'settingsAfter':m.current_simctl_settings(identifier)}
  record['runs'].append(row);(e/'diagnostic.json').write_text(json.dumps(record,indent=2))
  assert row['settingsAfter']==previous
  assert m.directory_hash(Path(build['products']))==build['productSha256']
except Exception as error:record['error']=str(error);record['traceback']=traceback.format_exc()
finally:
 m.ROOT=root;m.IOS_ROOT=root/'ios/ACEClientApp';m.PROJECT=m.IOS_ROOT/'ACEClientApp.xcodeproj'
 record['restorationErrors']=m.restore_simctl_settings(identifier,previous,e,'iPhone 17 Pro Max')
 record['originalCandidateUnchanged']=m.candidate()==original
 record['finished']=time.time();(e/'diagnostic.json').write_text(json.dumps(record,indent=2))
print(json.dumps({'runs':[{k:r[k] for k in ['name','nativeExit','failedTests','passedTests']} for r in record['runs']],'error':record.get('error'),'evidence':str(e)}))
raise SystemExit(0 if len(record['runs'])==1 and not record.get('error') and record['originalCandidateUnchanged'] and not record['restorationErrors'] else 1)
