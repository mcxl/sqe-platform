import datetime, hashlib, json, pathlib, subprocess
root=pathlib.Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
variant=pathlib.Path('LOCAL_HOME/Developer/sqe-platform-r5-diagnostic')
stage=pathlib.Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915/12-revision5-discriminating-diagnosis')
relative='ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift'
expected='41a4aa36b13b93ee65011ef8590d9aed0cdf69eac11cbde765c34942a6aca9f1'
patch=stage/'variant/ACEClientAppUITests.r5-d1.correction2.patch'
actual=subprocess.check_output(['git','-C',str(variant),'diff','--',relative])
assert hashlib.sha256(actual).hexdigest()==expected
assert actual==patch.read_bytes()
assert subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()=='52b212aca02190ee0e742debe383fa6016fe36b9'
assert not subprocess.check_output(['git','-C',str(root),'status','--porcelain'],text=True).strip()
subprocess.run(['git','-C',str(variant),'diff','--check'],check=True)
subprocess.run(['git','-C',str(root),'apply','--check',str(patch)],check=True)
source_hash=hashlib.sha256((variant/relative).read_bytes()).hexdigest()
assert source_hash=='d1970169effbfd0239d89d1ec1e770f5e670c2bd8560e1ada5333c2895e569b5'
review={'review':'Primary cumulative full diff inspection: original full variant, correction1 delta, correction2 delta',
 'recordedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'patchSha256':expected,'sourceSha256':source_hash,'correctionAttempt':2,
 'status':'Static review passed; compilation pending',
 'changes':['Use a nonoptional local attachmentName with the identical string for attachment.name and XCTContext.runActivity'],
 'checks':['Actual worktree diff equals retained reviewed patch','git diff --check passed','Full patch applies to clean live baseline','Live baseline clean and unchanged'],
 'diagnosticProceduresUnchanged':True,'applicationChanges':False,'nativeRuns':0,
 'stopRule':'If this corrective build fails, stop; no third corrective attempt'}
(stage/'variant/primary-static-review-correction-2.json').write_text(json.dumps(review,indent=2)+'\n')
print(json.dumps(review))
