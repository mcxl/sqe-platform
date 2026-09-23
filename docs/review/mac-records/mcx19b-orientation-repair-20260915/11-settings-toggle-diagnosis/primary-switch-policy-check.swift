import Foundation

enum Probe {
    enum NativeSwitchAction {
        case succeed
        case tap
        case fail
    }

    static func nativeSwitchAction(current: Bool?, expected: Bool, taps: Int) -> NativeSwitchAction {
        guard let current else { return .fail }
        if current == expected { return .succeed }
        return taps < 2 ? .tap : .fail
    }
}

func result(current: Bool?, taps: Int) -> String {
    switch Probe.nativeSwitchAction(current: current, expected: true, taps: taps) {
    case .succeed: return "succeed"
    case .tap: return "tap"
    case .fail: return "fail"
    }
}
let checks: [(String, Bool)] = [
    ("missed-first-input", result(current: false, taps: 0) == "tap" && result(current: false, taps: 1) == "tap" && result(current: true, taps: 2) == "succeed"),
    ("persistent-mismatch", result(current: false, taps: 0) == "tap" && result(current: false, taps: 1) == "tap" && result(current: false, taps: 2) == "fail"),
    ("already-desired", result(current: true, taps: 0) == "succeed"),
    ("unreadable", result(current: nil, taps: 0) == "fail")
]
for (name, passed) in checks {
    print("\(name): \(passed ? "pass" : "fail")")
    precondition(passed, "Unexpected action for \(name)")
}

for expected in [false,true] {
 for taps in 0...2 {
  let desired = Probe.nativeSwitchAction(current: expected, expected: expected, taps: taps)
  if case .succeed = desired {} else { fatalError("already requested must not tap") }
  let unknown = Probe.nativeSwitchAction(current: nil, expected: expected, taps: taps)
  if case .fail = unknown {} else { fatalError("unreadable must fail") }
  let wrong = Probe.nativeSwitchAction(current: !expected, expected: expected, taps: taps)
  if taps < 2 { if case .tap = wrong {} else { fatalError("bounded input missing") } }
  else { if case .fail = wrong {} else { fatalError("third input allowed") } }
 }
}
print("18 policy boundary checks passed; native delivery untested by this script")
