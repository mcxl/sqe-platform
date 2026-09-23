from pathlib import Path
import importlib.util,sys,json,os,time,datetime,shutil
os.umask(0o077)
stage=Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915')
root=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
d=stage/'10-target-size-diagnosis'
runs=list((d/'complete-pilot-runs').glob('*-pilot-*'));assert len(runs)==1,runs
run=runs[0]
spec=importlib.util.spec_from_file_location('pilot_integrity',root/'tools/ace_ios_local.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
started=time.monotonic()
candidate=json.loads((d/'clean-candidate.json').read_text())
execution=json.loads((d/'complete-pilot-execution.json').read_text())
assert execution['exit']==0 and execution['candidateUnchanged'] and execution['bootStatesRestored']
assert execution['candidate']==candidate and m.candidate()==candidate
manifest=run/'manifest.json';pilot=json.loads(manifest.read_text())
assert pilot['candidate']==candidate and pilot['mode']=='pilot'
m.validate_pilot_result(pilot)
assert (pilot['caseCount'],pilot['auditCount'],pilot['layoutCount'],pilot['auditInvocationCount'],pilot['nativeTestCount'])==(22,20,2,36,6)
assert pilot['executedCaseCount']==22 and pilot['reusedPilotCaseCount']==0
paths={role:Path(value['path']) for role,value in pilot['readinessEvidence'].items()}
assert m.pilot_readiness(candidate,paths)==pilot['readinessEvidence']
case_rows=[];batch_commands=[]
for batch in pilot['batches']:
 b=Path(batch['resultBundle']).parent
 assert batch['exit']==0
 for name,expected in [('result.xcresult',batch['resultBundleSha256']),('attachments',batch['attachmentSha256'])]:assert m.directory_hash(b/name)==expected
 for name,key in [('native.log','logSha256'),('native-summary.json','summarySha256'),('ACEClientAppUITests.xctestrun','runfileSha256')]:assert m.sha256(b/name)==batch[key]
 native=json.loads((b/'native-summary.json').read_text());assert native['passedTests']==1 and native['failedTests']==native['skippedTests']==native['expectedFailures']==0
 m.verify_screenshot_attachments(batch['caseRecords'],b/'attachments')
 command=json.loads((b/'native-command.json').read_text());assert command['exit']==0;batch_commands.append(command)
 for c in batch['caseRecords']:case_rows.append({'device':batch['device'],'batch':b.name,**c})
settings=[]
for p in sorted((run/'native-settings').iterdir()):
 native=json.loads((p/'summary.json').read_text());command=json.loads((p/'command.json').read_text())
 assert native['passedTests']==1 and native['failedTests']==native['skippedTests']==native['expectedFailures']==0 and command['exit']==0
 records=m.marker_records(p/'native.log',m.SETTINGS_MARKER);assert len(records)==1
 settings.append({'phase':p.name,'record':records[0],'seconds':command['seconds'],'bundleSha256':m.directory_hash(p/'result.xcresult'),'attachmentSha256':m.directory_hash(p/'attachments'),'commandSha256':m.sha256(p/'command.json'),'summarySha256':m.sha256(p/'summary.json'),'logSha256':m.sha256(p/'native.log')})
assert len(settings)==10
for device in m.DEVICES:
 before=next(v['record']['observed'] for v in settings if v['phase']==device+'-read')
 after=next(v['record']['observed'] for v in settings if v['phase']==device+'-restore-batch')
 assert before==after
for p in sorted((run/'restoration').glob('*readback.json')):
 restoration_data=json.loads(p.read_text());assert restoration_data['expected']==restoration_data['observed']
for p in sorted((run/'restoration').glob('*commands.json')):assert all(x['exit']==0 for x in json.loads(p.read_text()))
captures,max_batch=m.pilot_capture_measurements(pilot)
image_hashes,max_case_images,max_unmapped=m.pilot_image_measurements(pilot,captures)
reused=m.eligible_pilot_cases(pilot)
remaining=tuple(c for c in m.coverage_cases() if m.canonical_case(c.device,c.scenario,c.settings.payload()) not in reused)
remaining_batches=m.coverage_batches(remaining)
products=Path(pilot['build']['products']);scratch=m.directory_bytes(products)
projected=len(remaining)*max_batch
free=shutil.disk_usage(root).free
projection={'purpose':'Measurement only; no836-case run authorised by this goal','remainingCases':len(remaining),'remainingBatches':len(remaining_batches),'pilotMaxRawBatchBytes':max_batch,'rawPerRemainingCaseUpperBoundBytes':max_batch,'remainingRawEvidenceBytes':projected,'pilotMaxCaseImageCount':max_case_images,'pilotMaxUnmappedBatchImageCount':max_unmapped,'remainingImageCount':len(remaining)*max_case_images+len(remaining_batches)*max_unmapped,'scratchBytes':scratch,'requiredFreeBytes':2*projected+scratch+m.MIN_FREE_BYTES,'observedMacFreeBytes':free,'storageThresholdPassed':free>=2*projected+scratch+m.MIN_FREE_BYTES,'reviewThreshold':'Pending measured image inspection','limitation':'Largest observed batch used as a conservative per-case upper bound, not a measured per-case bundle size'}
record={'status':'passed native integrity; image inspection and archive retrieval remain separate','candidate':candidate,'verifiedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'manifest':str(manifest),'manifestSha256':m.sha256(manifest),'caseCount':22,'auditedCases':20,'layoutOnlyCases':2,'auditInvocations':36,'nativeCoverageTests':6,'nativeSettingsTests':len(settings),'unexpectedSkips':0,'sourceUnchanged':True,'restorationPassed':True,'nativeCoverageSeconds':sum(x['seconds'] for x in batch_commands),'nativeSettingsSeconds':sum(x['seconds'] for x in settings),'buildSecondsDuringPilot':0,'reusedBuildOriginalSeconds':json.loads((Path(pilot['build']['buildLog']).parent/'build-command.json').read_text())['seconds'],'nativeCaptureCount':sum(len(list(Path(b['attachmentDirectory']).glob('*.png'))) for b in pilot['batches']),'uniqueImageHashes':sorted(image_hashes),'resourceProjection':projection,'caseRecords':case_rows,'settings':settings,'integrityVerificationSeconds':round(time.monotonic()-started,3)}
with (d/'complete-pilot-native-integrity.json').open('x') as stream:json.dump(record,stream,indent=2)
print(json.dumps({k:v for k,v in record.items() if k not in {'caseRecords','settings','uniqueImageHashes'}},indent=2))
