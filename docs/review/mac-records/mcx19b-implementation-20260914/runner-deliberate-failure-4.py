from pathlib import Path
import hashlib,json,os,subprocess,time
base=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914')
root=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
source=root/'ios/ACEClientApp/ACEClientAppTests/ACEClientAppTests.swift'
original=source.read_bytes()
needle=b'XCTAssertEqual(request.httpMethod, "GET")'
assert original.count(needle)==1
changed=original.replace(needle,b'XCTAssertEqual(request.httpMethod, "POST")')
backup=base/'runner-deliberate-original-test-4.swift'
assert not backup.exists()
backup.write_bytes(original)
record={'runnerSha256':hashlib.sha256((root/'tools/ace_ios_local.py').read_bytes()).hexdigest(),'reviewCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'question':'Does the updated selected-test runner retain the deliberately incorrect POST expectation and actual GET result?','selector':'ACEClientAppTests/ACEClientAppTests/testRequestIsGETAndHasNoCache','expected':'POST','actualExpected':'GET','sourceOriginalSha256':hashlib.sha256(original).hexdigest(),'sourceProbeSha256':hashlib.sha256(changed).hexdigest(),'started':time.time()}
source.write_bytes(changed)
code=99
try:
    env=dict(os.environ,PYTHONPYCACHEPREFIX=str(base/'python-cache'))
    with (base/'runner-deliberate-failure-4.log').open('w') as out:
        code=subprocess.call(['/Library/Frameworks/Python.framework/Versions/3.14/bin/python3',str(root/'tools/ace_ios_local.py'),'selected','--diagnostic-dirty','--device','iPhone 17 Pro Max','--test',record['selector']],cwd=root,env=env,stdout=out,stderr=subprocess.STDOUT)
    record['runnerExit']=code
finally:
    if source.read_bytes()!=changed:
        record['restoreError']='Source changed during the diagnostic; automatic restore withheld'
    else:
        source.write_bytes(original)
        record['restoredSha256']=hashlib.sha256(source.read_bytes()).hexdigest()
    record['finished']=time.time()
    (base/'runner-deliberate-failure-4.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record))
raise SystemExit(code)
