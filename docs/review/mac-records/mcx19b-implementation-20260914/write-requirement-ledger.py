from pathlib import Path
import json,re,sys,hashlib,importlib.util,datetime,collections
base=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914')
root=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
functional=Path(sys.argv[1]).resolve()
assert functional.is_relative_to(base)
spec=importlib.util.spec_from_file_location('ace_runner',root/'tools/ace_ios_local.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
candidate=m.candidate(allow_dirty=True)
source=root/'docs/specs/2026-08-24-ace-ios-read-only-client-application.md'
requirements=[]
for n,line in enumerate(source.read_text().splitlines(),1):
 match=re.fullmatch(r'- `(IOS-[A-Z]+-\d{3})`: (.+)',line)
 if match:requirements.append((match.group(1),match.group(2),n))
assert len(requirements)==len({r[0] for r in requirements})==197
catalogue=(root/'ios/ACEClientApp/ACEClientAppTests/AcceptanceEvidenceCatalogue.swift').read_text()
mapping={i:'test'+name[0].upper()+name[1:] for i,name in re.findall(r'\.init\(identifier: "([^"]+)", test: "([^"]+)"\)',catalogue)}
assert set(mapping)=={x[0] for x in requirements}
runtime=json.loads((root/'ios/ACEClientApp/RuntimeEvidencePlan.json').read_text())
runtime_rows={i:e for e in runtime['entries'] for i in e['identifiers']}
assert len(runtime_rows)==44
checks={}
def visit(nodes):
 for node in nodes:
  if node.get('nodeType')=='Test Case' and 'AcceptanceEvidenceContractTests/' in node.get('nodeIdentifier',''):
   checks[node['name'].removesuffix('()')]=node['result']
  visit(node.get('children',[]))
visit(json.loads((functional/'tests.json').read_text())['testNodes'])
evidence=json.loads((functional/'functional-evidence.json').read_text())
entries=[]
for identifier,requirement,line in requirements:
 entry={'identifier':identifier,'requirement':requirement,'specificationLine':line,'status':'pending','reason':'Final acceptance has not run on one clean candidate. Focused checks are supporting evidence only.','mappedContractTest':mapping[identifier],'mappedTestResult':checks.get(mapping[identifier],'not found'),'mappedTestEvidence':str(functional/'tests.json'),'testResultLimit':'A passing mapped test does not prove the whole requirement. Source, fake-adapter and pending-record tests have limited scope.'}
 if identifier in runtime_rows:entry['requiredRuntimeProcedure']=runtime_rows[identifier]
 if identifier=='IOS-BASE-001':entry.update(status='blocked',reason='The historical baseline and verified iOS import have no common ancestor. A specific baseline decision is pending.',blockingEvidence=str(base/'baseline-provenance.json'))
 if identifier in ['IOS-ACC-008','IOS-ACC-011']:entry.update(status='blocked',reason='Retained native audit failures remain unresolved. Later passing diagnostics do not establish a correction or exception.',blockingEvidence=str(base/'release-current-build/result.xcresult'))
 entries.append(entry)
record={'createdAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate':candidate,'finalCandidateFrozen':False,'specification':str(source),'specificationSha256':m.sha256(source),'requirementCount':197,'statusCounts':dict(collections.Counter(e['status'] for e in entries)),'functionalEvidence':str(functional/'functional-evidence.json'),'functionalEvidenceCandidate':evidence['candidate'],'functionalCandidateMatchesCurrent':evidence['candidate']==candidate,'functionalSourceHashesMatchCurrent':evidence['candidate']['sourceHashes']==candidate['sourceHashes'],'functionalIOSSourceHashesMatchCurrent':{k:v for k,v in evidence['candidate']['sourceHashes'].items() if k.startswith('ios/')}=={k:v for k,v in candidate['sourceHashes'].items() if k.startswith('ios/')},'runtimeProcedureCount':len(runtime_rows),'entries':entries}
(base/'requirement-status.json').write_text(json.dumps(record,indent=2))
lines=['# ACE iOS Requirement Status','','This is an implementation checkpoint. It is not final acceptance.','',f"Current commit: `{candidate['commit']}`. The current worktree status is recorded in the candidate data; test execution identities remain separate.",'',f"All 197 identifiers are present. Status counts: {record['statusCounts']}.",'','Mapped test results describe individual checks only. Pending-record tests do not prove runtime behaviour.','','| Requirement | Status | Mapped Check | Check Result |','| --- | --- | --- | --- |']
lines += [f"| {e['identifier']} | {e['status']} | {e['mappedContractTest']} | {e['mappedTestResult']} |" for e in entries]
(base/'REQUIREMENT_STATUS.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({k:record[k] for k in ['requirementCount','statusCounts','runtimeProcedureCount','functionalCandidateMatchesCurrent']}))
