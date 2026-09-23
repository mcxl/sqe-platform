from pathlib import Path
import subprocess,json,hashlib,time,os
base=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914/negative-build-inputs')
base.mkdir(mode=0o700,exist_ok=False)
root=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
project=root/'ios/ACEClientApp/ACEClientApp.xcodeproj/project.pbxproj'
record={'question':'Does the native build reject missing and HTTP-only origin input in Validate Preview Inputs?', 'started':time.time(),'projectSha256':hashlib.sha256(project.read_bytes()).hexdigest(),'results':[]}
env={key:os.environ[key] for key in ['HOME','TMPDIR','USER','LOGNAME'] if key in os.environ}
env['PATH']='/usr/bin:/bin:/usr/sbin:/sbin'
for name,origin in [('missing-origin',''),('http-origin','http://preview.example.invalid')]:
 e=base/name;e.mkdir()
 cmd=['xcodebuild','build','-project',str(root/'ios/ACEClientApp/ACEClientApp.xcodeproj'),'-scheme','ACEClientApp','-configuration','Debug','-sdk','iphonesimulator','-destination','generic/platform=iOS Simulator','-derivedDataPath',str(e/'derived'),'-resultBundlePath',str(e/'result.xcresult'),'ACE_PREVIEW_ORIGIN='+origin,'ACE_BUNDLE_IDENTIFIER=com.example.aceclientapp','ARCHS=x86_64','ONLY_ACTIVE_ARCH=YES','CODE_SIGN_IDENTITY=','CODE_SIGNING_REQUIRED=NO','CODE_SIGNING_ALLOWED=NO']
 started=time.time()
 with (e/'build.log').open('w') as out:code=subprocess.call(cmd,cwd=root,env=env,stdout=out,stderr=subprocess.STDOUT)
 log=(e/'build.log').read_text(errors='replace')
 expected='error: ACE_PREVIEW_ORIGIN must be an approved HTTPS origin'
 item={'case':name,'command':cmd,'started':started,'finished':time.time(),'exit':code,'expectedError':expected,'actualErrors':[line.strip() for line in log.splitlines() if line.strip().startswith('error:')],'passed':code!=0 and expected in log and 'Validate' in log and (e/'result.xcresult').is_dir(),'evidence':str(e),'logSha256':hashlib.sha256((e/'build.log').read_bytes()).hexdigest()}
 record['results'].append(item)
 print(json.dumps(item),flush=True)
 if not item['passed']:break
record['finished']=time.time();record['projectUnchanged']=hashlib.sha256(project.read_bytes()).hexdigest()==record['projectSha256'];record['passed']=len(record['results'])==2 and all(r['passed'] for r in record['results']) and record['projectUnchanged']
(base/'results.json').write_text(json.dumps(record,indent=2))
raise SystemExit(0 if record['passed'] else 1)
