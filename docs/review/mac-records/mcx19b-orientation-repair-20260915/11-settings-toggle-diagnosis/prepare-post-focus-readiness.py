from pathlib import Path
import json,hashlib,subprocess,datetime,importlib.util,sys
r=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
s=Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915')
d=s/'11-settings-toggle-diagnosis';old=s/'10-target-size-diagnosis'
spec=importlib.util.spec_from_file_location('settings_readiness',r/'tools/ace_ios_local.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
c=m.candidate();assert c['status']=='clean'
focus=d/'native-settings-on-off-v1'
fx=json.loads((focus/'execution.json').read_text())
assert fx['exit']==0 and fx['candidateUnchanged'] and fx['bootStatesRestored'] and not fx['restorationFailures']
assert fx['candidate']['commit']=='af8c82dc2e7e3faec77e03d8d902e1642943f29c'
assert json.loads((focus/'acceptance.json').read_text())['status']=='passed'
assert c['commit']!=fx['candidate']['commit']
delta=subprocess.check_output(['git','-C',str(r),'diff',fx['candidate']['commit'],c['commit'],'--'],text=True)
assert delta==(d/'DIAG11/DIAG11-v2-incremental-af8c82d.patch').read_text()
oldc=json.loads((old/'clean-candidate.json').read_text())
changed=[k for k in set(oldc['sourceHashes'])|set(c['sourceHashes']) if oldc['sourceHashes'].get(k)!=c['sourceHashes'].get(k)]
assert changed==['ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift']
path=changed[0]
before=subprocess.check_output(['git','-C',str(r),'show',oldc['commit']+':'+path],text=True)
after=(r/path).read_text()
assert before.split('    private func setNativeAccessibilityToggle(',1)[0]==after.split('    private enum NativeSwitchAction',1)[0]
assert before.split('    private func returnToSettingsRoot(',1)[1]==after.split('    private func returnToSettingsRoot(',1)[1]
def section(text,start,end):
 return text[text.index(start):text.index(end,text.index(start))]
pairs=[('    func testConfigureAccessibilitySettings()', '    private func decodedCoverageCases('),
       ('    private func captureCoverageViewport(', '    private func runCoverageAudit('),
       ('    private func addScreenshot(', '    private func assertMinimumActionTargets(')]
for start,end in pairs:assert section(before,start,end)==section(after,start,end)
def item(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
records=[]
for p in sorted((old/'readiness').glob('*.json')):
 x=json.loads(p.read_text())
 for v in x['evidence']:
  q=Path(v['path']);assert item(q)['sha256']==v['sha256']
 records.append(item(p))
impact={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate':c['commit'],'base':oldc['commit'],'changedFiles':changed,'scope':'Only Settings desired-state retry and attempt diagnostics changed. App, runner, native audit, capture, coverage and unit/model/contract paths remain unchanged.','unchangedSections':[x[0] for x in pairs],'focusActualCandidate':fx['candidate']['commit'],'postFocusDelta':item(d/'DIAG11/DIAG11-v2-incremental-af8c82d.patch'),'focusedReuse':'The final delta only corrects failure wording for unreadable/exhausted control; successful on/off paths and decision policy are identical. Native focus is attributed to its actual af8 head, not the new head.','captureGateReuse':'The deliberate negative capture at c8 and positive medium case at c0 retain the same app/capture/extraction path. Settings recovery is checked separately. Historical failure evidence remains unchanged.','functionalReuse':'68 native model/unit/contract passes, including43contracts, remain attributable to actual a84 head and prior checked source hashes; app/unit/project inputs unchanged from c0.','priorReadinessRecords':records,'limitation':'Full22 acceptance requires the new clean candidate. Apple missed-input cause remains unresolved. No phone/service/836 acceptance.'}
(d/'source-impact-and-reuse.json').write_text(json.dumps(impact,indent=2)+'\n')
(d/'clean-candidate.json').write_text(json.dumps(c,indent=2)+'\n')
roles={}
out=d/'readiness';out.mkdir(exist_ok=True)
for role in m.READINESS_ROLES:
 x=json.loads((old/'readiness'/(role+'-readiness.json')).read_text())
 x['candidate']=c;x['recordedUTC']=impact['UTC'];x['scope']+=' Current update: bounded Settings recovery; native on/off actual af8 proof plus diagnostics-only final delta. See source-impact record.'
 x['evidence'].append(item(d/'source-impact-and-reuse.json'))
 x['evidence'].append(item(focus/'acceptance.json'))
 if role=='pocock':
  for name in ['standards-review-v2.json','spec-review.json','primary-complete-goal-diff.patch','review-repair-integration.json']:
   x['evidence'].append(item(d/name))
 if role=='evidence-gate':
  x['evidence'].append(item(focus/'native-evidence-integrity.json'))
 p=out/(role+'-readiness.json');p.write_text(json.dumps(x,indent=2)+'\n');roles[role]=p
v=m.pilot_readiness(c,roles);(d/'validated-readiness.json').write_text(json.dumps(v,indent=2)+'\n')
print(json.dumps({'candidate':c['commit'],'readiness':'passed','focusActualCandidate':fx['candidate']['commit'],'scope':'22pilot only'}))
