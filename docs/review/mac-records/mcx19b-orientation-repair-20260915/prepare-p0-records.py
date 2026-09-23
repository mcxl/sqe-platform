import difflib,hashlib,json,pathlib,subprocess
r=pathlib.Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
e=pathlib.Path('LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915/13-p0-discovery-runner-20260917')
e.mkdir(exist_ok=True)
changes={}
def replace(name,old,new):
 before,after=changes.get(name,((r/name).read_text(),(r/name).read_text()))
 assert after.count(old)==1,(name,old[:100],after.count(old))
 changes[name]=(before,after.replace(old,new,1))
new_plan='''# ACE iOS Discovery Candidate

## Authority And Scope

This record describes the planned verification of the Swift discovery candidate. It reports no future gate as passed.

The approved 16 September instruction is Revision 5, SHA-256 `252aab6ba1115b72f1fcbd84c3d49f3429550c0845d96c2008088d15bdbbe629`.
Alan subsequently approved closing Arm C as incomplete and moving to the runner step on 17 September.
The new runner work block starts at `2026-09-16T20:50:47Z` and ends at `2026-09-16T21:50:47Z`.
This transition does not renew D1, waive an audit finding or change acceptance coverage.

The candidate is prepared on `codex/mcx19b-release-layout`, from `52b212aca02190ee0e742debe383fa6016fe36b9`.
Record the eventual clean commit and source hashes outside the repository after the P0 commit.
Do not infer historical baseline ancestry. That decision still blocks final acceptance and merge.

## Chosen Product Route

Continue the existing Swift application and its current complete-action Copy design.
Expo and Bolt are closed alternatives for this task. Existing Swift source and retained native evidence support continuing this implementation.
The intermittent audit finding does not establish a framework defect. A rebuild would require new implementation and verification evidence.
Codemagic, paid membership, TestFlight, App Store submission, new server development and Production remain excluded.

## Candidate Changes

The runner gains an explicit discovery option for the existing 22-case pilot.
Each case runs independently. A failed case remains failed and keeps its native evidence.
Later cases may continue only when the preceding case has complete evidence and the environment is usable.
Missing evidence, unexpected test counts or skips, failed launch, infrastructure failure and failed restoration stop discovery.
Discovery must not grant acceptance credit. Default acceptance behaviour and unrestricted native audits remain unchanged.

The temporary D1 split-audit and positioning procedures are not imported into the candidate.
Application source, UI assertions, fixtures, authentication, Keychain, clipboard rules and API contracts remain unchanged by this runner work.
The development state, progress guide and specification references are prepared before freezing the candidate.

## Required Verification

1. Verify focused runner tests for continuation, retained failure, stop conditions and acceptance compatibility.
2. Inspect the complete candidate diff and obtain a fresh Sol review.
3. Confirm the deliberate-failure and corrected-pass evidence gate after relevant runner changes.
4. Commit only task files and record the clean candidate identity externally.
5. Run the required 68 unit and contract tests, including the 43-test contract subset, on that candidate.
6. Run the 22-case discovery pilot and retain every passed, failed or blocked outcome.
7. Classify failures before corrective changes. Keep the original unexplained Copy finding open.

Discovery is a learning run. It cannot replace the final 22-case acceptance pilot or the 836-case programme.
Final verification requires Pocock review on the frozen candidate, then the controlling plan's acceptance and review gates.
The required programme remains 512 unrestricted audit cases and 324 layout-only cases.
Keep the nine regression selectors, physical iPhone 15 Pro Max checks, signing, approved service and review evidence.

## Evidence And Freeze

The [local verification plan](2026-09-14-ace-ios-local-verification.md) controls coverage, storage, privacy and final acceptance.
The [application specification](../specs/2026-08-24-ace-ios-read-only-client-application.md) remains authoritative for product behaviour.
P0 evidence stays under `LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915/13-p0-discovery-runner-20260917`.
D1's disposition is retained at `08-copy-confirmation-diagnosis/discriminating-diagnostic-result.json` under the same parent evidence root.
Keep its failed placement result and unresolved contrast finding visible. Do not reinterpret incomplete Arm C as passed.

After freeze, store results and review records outside the candidate. Reference run paths and hashes from the review records.
Any application, test, runner, workflow or repository-record change creates a new candidate and renews affected final gates.
Do not merge or deploy to Production under this authority.
'''
name='docs/plans/2026-09-17-ace-ios-discovery-candidate.md';assert not (r/name).exists();changes[name]=('',new_plan)
replace('DEV_STATE.md','## Controlled Branch\n\nThe current delivery branch is `codex/sqe-pivot-integration`.\nIts baseline is the sanitised SQE Platform repository root.',
'''## Current ACE iOS Candidate

The current ACE iOS delivery branch is `codex/mcx19b-release-layout` on the approved Mac.
The discovery candidate is prepared from `52b212aca02190ee0e742debe383fa6016fe36b9`.
Continue the Swift application. Expo, Bolt and Codemagic are outside the approved route.

See [ACE iOS Discovery Candidate](docs/plans/2026-09-17-ace-ios-discovery-candidate.md) for planned verification and freeze rules.
This record does not establish acceptance. The original Copy contrast finding and baseline ancestry decision remain unresolved.
Retain the 22-case pilot, 836-case programme, physical-device, service, signing and review requirements.
Keep results outside the frozen candidate and bind each result to its tested identity.

## Historical Platform Integration Context

The earlier platform delivery branch was `codex/sqe-pivot-integration`.
Its baseline was the sanitised SQE Platform repository root.''')
replace('DEV_STATE.md','## Current Delivery Goal','## Historical Platform Delivery Goal')
replace('docs/plans/2026-09-14-ace-ios-local-verification.md','## Local Runner And Evidence',
'''## Discovery Transition — 17 September 2026

The user approved closing the D1 positioning experiment as incomplete and proceeding to P0 runner work.
The [discovery candidate record](2026-09-17-ace-ios-discovery-candidate.md) defines the change, bounded work block and planned verification.
This does not waive the unresolved Copy finding or reduce final acceptance requirements.

Discovery runs each pilot case independently and preserves every native failure.
It stops on lost evidence, unexpected or incomplete native execution, failed launch, infrastructure faults or failed restoration.
A completed discovery run with failures is not acceptance. The default acceptance pilot still requires every gate to pass.
No D1 diagnostic procedure enters the application or committed UI tests under this transition.

## Local Runner And Evidence''')
replace('docs/specs/2026-08-24-ace-ios-read-only-client-application.md',
'The current local verification record gives the complete matrix, pilot, resource, runner, diagnostic, and renewal controls: [ACE iOS Local Verification](../plans/2026-09-14-ace-ios-local-verification.md).',
'''The current local verification record gives the complete matrix, pilot, resource, runner, diagnostic, and renewal controls: [ACE iOS Local Verification](../plans/2026-09-14-ace-ios-local-verification.md).

The approved [Discovery Candidate](../plans/2026-09-17-ace-ios-discovery-candidate.md) adds a diagnostic pilot execution mode. Failed cases stay failed. This mode cannot satisfy the acceptance pilot or waive any accessibility requirement. The 836-case coverage and final acceptance gates remain unchanged.''')
replace('ACE_PROGRESS_GUIDE.html','<p class="muted">Last updated: 25 August 2026</p>',
'''<p class="muted">ACE iOS candidate plan updated: 17 September 2026. Earlier delivery records below remain historical.</p>

  <div class="section">
    <h2>Current ACE iOS Candidate</h2>
    <p>Continue the Swift app on <code>codex/mcx19b-release-layout</code>, prepared from <code>52b212aca02190ee0e742debe383fa6016fe36b9</code>.</p>
    <p>The planned discovery runner records all 22 pilot outcomes while keeping failed cases failed. It stops on evidence, launch or environment faults.</p>
    <p>No acceptance is claimed. The Copy contrast finding and baseline ancestry decision remain open. Required coverage remains 836 cases.</p>
    <p><a href="docs/plans/2026-09-17-ace-ios-discovery-candidate.md">Candidate and planned verification</a> · <a href="docs/plans/2026-09-14-ace-ios-local-verification.md">Controlling local plan</a></p>
  </div>''')
replace('ACE_PROGRESS_GUIDE.html','<h2>Overall Status</h2>','<h2>Historical Specification Delivery Status — August 2026</h2>')
replace('ACE_PROGRESS_GUIDE.html','The issue remains <code>Todo</code> and is not approved for implementation.',
'This was the August issue status. The current Swift implementation authority and planned verification are recorded in the candidate plan above.')
start='''      <tr><th>Build And Automated Tests</th><td>After provider approval, Codemagic receives only the approved private source. It uses Xcode 26 for builds and automated tests.</td></tr>
      <tr><th>Simulator Evidence</th><td>Revyl receives only the compiled simulator <code>.app</code>. It provides the required iOS 26 simulator evidence.</td></tr>
      <tr><th>Final Device Evidence</th><td>Use the approved Mac and an iPhone 15 Pro or later model.</td></tr>'''
replace('ACE_PROGRESS_GUIDE.html',start,'''      <tr><th>Build And Automated Tests</th><td>Use the approved Mac and local Xcode 26.4.1 workflow. Windows controls work and reviews compact records.</td></tr>
      <tr><th>Simulator Evidence</th><td>Use iPhone 17 and iPhone 17 Pro Max on iOS 26.4.1. Keep bulk evidence in private Mac storage.</td></tr>
      <tr><th>Final Device Evidence</th><td>Use the already approved iPhone 15 Pro Max, with current free signing and required manual checks.</td></tr>
      <tr><th>Closed Alternatives</th><td>Continue Swift. Expo and Bolt would require replacement implementation and new evidence; no framework cause has been established. Codemagic is excluded.</td></tr>''')
start=changes['ACE_PROGRESS_GUIDE.html'][1].index('    <h2>Next Steps</h2>')
end=changes['ACE_PROGRESS_GUIDE.html'][1].index('  </div>',start)
old=changes['ACE_PROGRESS_GUIDE.html'][1][start:end]
replace('ACE_PROGRESS_GUIDE.html',old,'''    <h2>Next Steps</h2>
    <ul>
      <li><strong>Runner:</strong> Implement discovery mode, verify failure handling and obtain the required fresh review.</li>
      <li><strong>Freeze:</strong> Complete candidate records, commit only task files and retain the clean candidate identity externally.</li>
      <li><strong>Pilot:</strong> Complete the 22-case discovery pilot. Preserve and classify every failure before corrections.</li>
      <li><strong>Acceptance:</strong> Obtain Pocock review before final verification. Require the acceptance pilot and all 836 cases to pass.</li>
      <li><strong>Device And Service:</strong> Complete signing, physical iPhone, private-service, baseline and remaining review gates.</li>
    </ul>
    <p>Keep fictional-only data and G0 controls. No real client data, Production deployment or automatic merge.</p>
''')
patch=''.join(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+n if old else '/dev/null',tofile='b/'+n)) for n,(old,new) in changes.items())
data=patch.encode();(e/'candidate-records.patch').write_bytes(data)
subprocess.run(['git','-C',str(r),'apply','--check','-'],input=data,check=True)
subprocess.run(['git','-C',str(r),'apply','-'],input=data,check=True)
subprocess.run(['git','-C',str(r),'diff','--check'],check=True)
print(json.dumps({'files':list(changes),'patchSha256':hashlib.sha256(data).hexdigest()}))
