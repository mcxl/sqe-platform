"""Build the approved diagnostic test variant; keep the application bundle fixed."""
import hashlib, importlib.util, json, pathlib, plistlib, subprocess, sys
ROOT=pathlib.Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
VARIANT=pathlib.Path('LOCAL_HOME/Developer/sqe-platform-r5-diagnostic')
STAGE=pathlib.Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915/12-revision5-discriminating-diagnosis')
spec=importlib.util.spec_from_file_location('ace_local', ROOT/'tools/ace_ios_local.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
pre=json.loads((STAGE/'preflight.json').read_text())
attempt=int(sys.argv[1]) if len(sys.argv)==2 else 0
assert attempt in (0,1,2),'Only the initial build and two bounded corrective attempts are permitted'
suffix='' if attempt==0 else f'-correction-{attempt}'
assert m.candidate()==pre['candidate']
assert subprocess.check_output(['git','-C',str(VARIANT),'rev-parse','HEAD'],text=True).strip()==pre['candidate']['commit']
modified=subprocess.check_output(['git','-C',str(VARIANT),'diff','--name-only'],text=True).splitlines()
assert modified==['ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift'],modified
assert not subprocess.run(['pgrep','-x','xcodebuild'],capture_output=True,text=True).stdout.strip()
for relative,expected in pre['candidate']['sourceHashes'].items():
    if relative.startswith('ios/ACEClientApp/ACEClientApp/'):
        assert m.sha256(VARIANT/relative)==expected,relative
patch=subprocess.check_output(['git','-C',str(VARIANT),'diff','--',modified[0]])
review=json.loads((STAGE/f'variant/primary-static-review{suffix}.json').read_text())
assert hashlib.sha256(patch).hexdigest()==review['patchSha256'],'Unreviewed diagnostic patch'
assert m.directory_hash(pathlib.Path(pre['build']['products']))==pre['build']['productSha256'],'Original build products changed'
evidence=STAGE/f'variant-build{suffix}'
evidence.mkdir(exist_ok=False)
(evidence/'reviewed-test-variant.patch').write_bytes(patch)
m.ROOT=VARIANT;m.IOS_ROOT=VARIANT/'ios/ACEClientApp';m.PROJECT=m.IOS_ROOT/'ACEClientApp.xcodeproj'
variant_sources=dict(pre['candidate']['sourceHashes'])
variant_sources[modified[0]]=m.sha256(VARIANT/modified[0])
variant_identity={'commit':pre['candidate']['commit'],'sourceHashes':variant_sources,
 'workingTree':str(VARIANT),'diagnosticOnly':True,
 'gitStatus':subprocess.check_output(['git','-C',str(VARIANT),'status','--porcelain'],text=True),
 'patchSha256':hashlib.sha256(patch).hexdigest()}
record=m.build(variant_identity,evidence)
raw_template=pathlib.Path(record['template'])
original_template=pathlib.Path(pre['build']['template'])
original=plistlib.loads(original_template.read_bytes())['ACEClientAppUITests']
def original_paths(value):
    if isinstance(value,str): return value.replace('__TESTROOT__',str(original_template.parent))
    if isinstance(value,list): return [original_paths(v) for v in value]
    if isinstance(value,dict): return {k:original_paths(v) for k,v in value.items()}
    return value
original=original_paths(original)
app=pathlib.Path(original['UITargetAppPath'])
assert app.is_dir()
app_hash=m.directory_hash(app)
for arm in ('B','C'):
    target_file=STAGE/f'arm-{arm}.xctestrun'
    m.configure_xctestrun(raw_template,target_file,{'ACE_D1_ARM':arm})
    payload=plistlib.loads(target_file.read_bytes());target=payload['ACEClientAppUITests']
    variant_app=target['UITargetAppPath']
    target['UITargetAppPath']=str(app)
    target['UITargetAppEnvironmentVariables']=original['UITargetAppEnvironmentVariables']
    target['DependentProductPaths']=[str(app) if v==variant_app else v for v in target['DependentProductPaths']]
    target_file.write_bytes(plistlib.dumps(payload,sort_keys=True))
    out={**record,'template':str(target_file),'identity':m.sha256(target_file),'diagnosticArm':arm,
         'applicationBundle':str(app),'applicationBundleSha256':app_hash,
         'testSourceSha256':m.sha256(VARIANT/modified[0]),
         'patchSha256':hashlib.sha256(patch).hexdigest(),
         'diagnosticOnly':True,'pilotCredit':0}
    (STAGE/f'arm-{arm}-build.json').write_text(json.dumps(out,indent=2)+'\n')
assert m.directory_hash(app)==app_hash
print(json.dumps({'status':'built diagnostic tests','applicationBundleSha256':app_hash,
 'testSourceSha256':out['testSourceSha256'],'patchSha256':out['patchSha256']}),flush=True)
