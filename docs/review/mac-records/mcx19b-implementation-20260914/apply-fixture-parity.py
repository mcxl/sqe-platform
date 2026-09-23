from pathlib import Path
import hashlib,json,difflib,sys,os
os.umask(0o077)
r=Path('LOCAL_HOME/Developer/sqe-platform-release-layout')
b=Path('LOCAL_HOME/ace-private/mcx19b-implementation-20260914')
changes={}
def replace(text,old,new,count=1):
    assert text.count(old)==count,(old,text.count(old))
    return text.replace(old,new)
p=r/'ios/ACEClientApp/ACEClientApp/Views.swift'
old=p.read_text();new=old
new=replace(new,'CurrentReleaseMessageView(message: message, retry: .refresh, state: state)','CurrentReleaseMessageView(message: message, retry: .refresh, retryAction: state.refresh, signOutAction: state.signOut)')
new=replace(new,'CurrentReleaseMessageView(message: message, retry: retry, state: state)','CurrentReleaseMessageView(message: message, retry: retry, retryAction: { state.retry(retry) }, signOutAction: retry == .refresh ? state.signOut : nil)')
a=new.index('struct CurrentReleaseMessageView: View {');z=new.index('struct SafeMessageView: View {',a)
section=new[a:z]
section=replace(section,'    @ObservedObject var state: SessionState','    let retryAction: () -> Void\n    let signOutAction: (() -> Void)?')
section=replace(section,'Button { state.retry(retry) } label:', 'Button { retryAction() } label:')
section=replace(section,'if retry == .refresh {','if let signOutAction {')
section=replace(section,'Button { state.signOut() } label:', 'Button { signOutAction() } label:')
new=new[:a]+section+new[z:]; changes[p]=(old,new)
p=r/'ios/ACEClientApp/ACEClientApp/DebugScenario.swift'
old=p.read_text();new=old
for message in ['No current release is available.','ACE is unavailable. Try again later.','ACE could not be reached. Check your connection and try again.','The request timed out. Try again.','ACE could not establish a secure connection. Try again later.']:
    phrase='SafeMessageView(message: "'+message+'", action: ("Refresh", {}))'
    new=replace(new,phrase,'CurrentReleaseMessageView(message: "'+message+'", retry: .refresh, retryAction: {}, signOutAction: {})',3 if message=='ACE is unavailable. Try again later.' else 1)
new=replace(new,'SafeMessageView(message: "Saved sign-in could not be read. Try again.", action: ("Try again", {}))','CurrentReleaseMessageView(message: "Saved sign-in could not be read. Try again.", retry: .keychainRead, retryAction: {}, signOutAction: nil)')
for message in ['Access denied. Sign in again.','Sign-in could not be saved. Try again.']:
    new=replace(new,'SafeMessageView(message: "'+message+'", action: nil)','SignInView(message: "'+message+'", submit: { _, _ in })')
new=replace(new,'case .loading: ProgressView("Loading")','case .loading: ProgressView("Loading").accessibilityLabel("Loading current release")')
changes[p]=(old,new)
p=r/'ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift'
old=p.read_text();new=old
new=replace(new,'        case "signIn":\n            return requireCoverage(app.secureTextFields["Password"].exists, "Password must be a secure field")','        case "signIn", "denied", "keychainWrite":\n            return requireCoverage(app.textFields["Username"].exists, "Username field must exist")\n                && requireCoverage(app.secureTextFields["Password"].exists, "Password must be a secure field")')
new=replace(new,'        case "signIn":\n            return ["Sign in"]','        case "signIn", "denied", "keychainWrite":\n            return ["Sign in"]')
new=replace(new,'            return ["Refresh"]\n        case "keychainRead", "keychainDeletion":\n            return ["Try again"]','            return ["Refresh current release", "Sign out"]\n        case "keychainRead":\n            return ["Retry saved sign-in read"]\n        case "keychainDeletion":\n            return ["Try again"]')
new=replace(new,'app.progressIndicators["Loading"]','app.progressIndicators["Loading current release"]')
new=replace(new,'("loading", "Loading")','("loading", "Loading current release")')
changes[p]=(old,new)
record={'reason':'Eleven DEBUG fixture names used different production view types or omitted recovery controls. Inject no-op actions into the same view types used by RootView. Production actions and screen layout are preserved. No SessionState, network, credential or server code changes.','files':{},'status':'prepared'}
for p,(old,new) in changes.items():
    rel=str(p.relative_to(r));record['files'][rel]={'before':hashlib.sha256(old.encode()).hexdigest(),'after':hashlib.sha256(new.encode()).hexdigest()}
    print(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=rel,tofile=rel)))
if '--apply' in sys.argv:
    for p,(old,new) in changes.items():
        assert p.read_text()==old
        backup=b/('before-fixture-parity-'+p.name)
        assert not backup.exists(),backup
        backup.write_text(old);p.write_text(new)
    record['status']='applied'
(b/'fixture-parity-correction.json').write_text(json.dumps(record,indent=2))
