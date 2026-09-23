from pathlib import Path
import hashlib,json,os,subprocess,time
base=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914')
root=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
source=root/'ios/ACEClientApp/ACEClientAppTests/ACEClientAppTests.swift'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='8bcd2da3c4bc53e65a2a05e7a3109bf66616b97993a32dd18aa108607111c4a3'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip()
record={'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'runnerSha256':hashlib.sha256((root/'tools/ace_ios_local.py').read_bytes()).hexdigest(),'question':'Does the same selected GET request test pass after exact restoration of its expectation?','selector':'ACEClientAppTests/ACEClientAppTests/testRequestIsGETAndHasNoCache','started':time.time()}
env=dict(os.environ,PYTHONPYCACHEPREFIX=str(base/'python-cache'))
with (base/'runner-corrected-pass-4.log').open('w') as out:
    code=subprocess.call(['/Library/Frameworks/Python.framework/Versions/3.14/bin/python3',str(root/'tools/ace_ios_local.py'),'selected','--device','iPhone 17 Pro Max','--test',record['selector']],cwd=root,env=env,stdout=out,stderr=subprocess.STDOUT)
record.update(runnerExit=code,finished=time.time(),finalSourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(),finalGitStatus=subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True))
(base/'runner-corrected-pass-4.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record))
raise SystemExit(code)
