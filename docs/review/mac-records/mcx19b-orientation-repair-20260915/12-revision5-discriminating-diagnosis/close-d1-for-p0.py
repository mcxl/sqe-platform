import datetime,hashlib,json,pathlib
root=pathlib.Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915')
s=root/'12-revision5-discriminating-diagnosis'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
observations={
 '15aae5e095e340276b06fb53db6e9513bc726795fc86cfff74af760670ac5a2e':'Scrolled Action 1: Copy and Copied Action 1 are fully visible; Refresh below; Sign out partly outside the scroll viewport.',
 'f357ef26634e990391a08a3a4da3952e29c90cd695259a02346d30d9dac0a7c9':'Initial release: details and conclusion readable; Action 1 starts near viewport bottom. No visible text overlap.',
 '756745365cd12b1c8fd18af14f5701f667f024373760486c70d2a0510261cc50':'Scrolled Action 1: Copy, confirmation, Refresh and Sign out readable. No visible overlap within the viewport.',
 'f7d435dfa828b5e7ae96441ad7079e6e32758003eb2bec95e6dcb82ba41caff5':'Initial release: details and conclusion readable; Action 1 continues below viewport. No visible text overlap.',
 '61085bbbbb55a4fa8a93a7722fe19f5bbe028d40200e7a2fb42ef55d3bd340ee':'Initial release: details and conclusion readable; Action 1 continues below viewport. No visible text overlap.',
 '211fc45228fdac1a6c73df3b235ecfbb5aabee39a8054065c9f140f2649c7e29':'Scrolled Action 1: Copy and confirmation readable in lower half; Refresh and Sign out readable beneath.',
 '95abec6bd25ef556356a46bb70b373e42464abd5d006b6e4e66485b3ef7fc940':'C1 retained scrolled state: Copy and confirmation visible in lower half; Refresh and Sign out beneath. This capture does not establish the final attempted placement.',
 '86149f3642bd8cbdfbb6433b0e97978d95eb959af6d6f92c76527928d75294b2':'C1 initial release state: details and conclusion readable; Action 1 starts near the viewport bottom.'}
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
for arm,n in [('B',3),('B',4),('B',5),('C',1)]:
 directory=s/f'arm-{arm}/repetition-{n}'
 images=[]
 for p in sorted((directory/'batches/001/attachments').glob('*.png')):
  digest=sha(p);assert digest in observations
  images.append({'path':str(p),'sha256':digest,'bytes':p.stat().st_size,'observation':observations[digest]})
 assert len(images)==2
 record={'status':'complete','recordedUTC':now,'reviewer':'primary agent','method':'Full-resolution PNGs streamed from Mac storage into image inspection; no Windows evidence files exported',
  'inspectedAtOriginalResolution':True,'images':images,'distinctPNGCount':len({i['sha256'] for i in images}),
  'limitations':['Still images do not establish audit sampling appearance, measured contrast, root cause or acceptance.','C1 post-copy audit did not execute. No final placement frame record exists.']}
 output=directory/'image-inspection.json';assert not output.exists();output.write_text(json.dumps(record,indent=2)+'\n')
runs=[]
for arm,count in [('A',5),('B',5),('C',1)]:
 for n in range(1,count+1):
  p=s/f'arm-{arm}/repetition-{n}/execution.json';d=read(p);i=p.parent/'image-inspection.json'
  assert i.exists() and d['candidateUnchanged'] and not d['restorationFailures']
  expected=2 if arm!='B' else 14
  calls=sum(c.get('auditInvocations',0) for c in d.get('batch',{}).get('caseRecords',[])) if arm=='A' else len(d.get('auditCalls',[]))
  runs.append({'arm':arm,'repetition':n,'nativeOutcome':d.get('nativeOutcome','PASSED' if d.get('batch',{}).get('exit')==0 else 'UNKNOWN'),
   'auditCalls':calls,'expectedAuditCalls':expected,'execution':str(p),'executionSha256':sha(p),'imageInspection':str(i),'imageInspectionSha256':sha(i),
   'candidateUnchanged':True,'restorationFailures':[],'startedUTC':d.get('startedUTC'),'finishedUTC':d.get('finishedUTC')})
assert sum(r['auditCalls'] for r in runs)==81
c=read(s/'arm-C/repetition-1/execution.json')
assert c['nativeSummary']['testFailures'][0]['failureText']=='failed - D1 C could not place Copy action 1 fully above the scroll viewport midpoint'
video=s/'c11-video/inspection.json'
result={'status':'D1 incomplete; stopped at C1; user authorised transition to P0 without an app or UI-test correction',
 'recordedUTC':now,'candidate':'52b212aca02190ee0e742debe383fa6016fe36b9',
 'approvedRevision5Sha256':'252aab6ba1115b72f1fcbd84c3d49f3429550c0845d96c2008088d15bdbbe629',
 'transitionAuthority':{'userResponse':'proceed','context':'Approval of closing Arm C as incomplete and moving to runner implementation with a fresh 60-minute limit',
 'newBlockStartUTC':'2026-09-16T20:50:47Z','newBlockDeadlineUTC':'2026-09-16T21:50:47Z','originalApprovalFileChanged':False},
 'runs':runs,'executedDiagnosticCases':11,'plannedDiagnosticCases':15,'unexecuted':['C2','C3','C4','C5'],
 'successfulDiagnosticCases':10,'failedDiagnosticCases':1,'observedAuditCalls':81,
 'countNote':'A:10 unrestricted calls; B:70 individual-type calls; C1:one initial unrestricted call. Calls are not separate cases. Settings helpers and builds are separate.',
 'findings':{'originalCopyContrast':'unresolved; historical failed pilot remains failed','newNativeAccessibilityFindings':[],
 'harnessFailure':{'test':'ACEClientAppUITests/testCoverageBatch()','source':'LOCAL_HOME/Developer/sqe-platform-r5-diagnostic/ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift','line':680,
 'expected':'Copy action 1 frame entirely above scroll viewport midpoint, followed by two identical frame reads and the post-copy audit',
 'actual':c['nativeSummary']['testFailures'][0]['failureText'],'nativeExit':65,
 'effect':'Placement failed; no C placement frame record; post-copy audit absent. Wrapper rejected incomplete audit-call sequence.',
 'wrapperMessage':c['error'],'classification':'diagnostic test prerequisite failure; not a new contrast finding'}},
 'videoInspection':{'path':str(video),'sha256':sha(video),'limitation':'No accessible frame reaches the logged finding time; no sample-time or cause claim.'},
 'allRetainedPNGsInspected':True,'imageReviewNote':'Missing B3-B5/C1 inspection records were completed by the primary during closeout. Original run records remain unchanged.',
 'noApplicationChanges':True,'noCommittedUITestChanges':True,'acceptanceCredit':0,'pilotCredit':0,
 'claimLimits':['Non-observation in ten successful diagnostic runs does not establish a fix.','C is incomplete, not passed.','No audit exception or scope reduction for the 836-case programme is approved.'],
 'next':'P0 discovery runner and focused checks, records, primary review, fresh Sol; native evidence gate before any pilot.'}
out=root/'08-copy-confirmation-diagnosis/discriminating-diagnostic-result.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'path':str(out),'sha256':sha(out),'cases':11,'audits':81,'status':result['status']}))
