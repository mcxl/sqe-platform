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

func result(current: Bool?, expected: Bool, taps: Int) -> String {
    switch Probe.nativeSwitchAction(current: current, expected: expected, taps: taps) {
    case .succeed: return "succeed"
    case .tap: return "tap"
    case .fail: return "fail"
    }
}
let checks: [(String, Bool)] = [
    ("desired-true-missed-first-then-success", result(current: false, expected: true, taps: 0) == "tap" && result(current: false, expected: true, taps: 1) == "tap" && result(current: true, expected: true, taps: 2) == "succeed"),
    ("desired-true-persistent-mismatch", result(current: false, expected: true, taps: 0) == "tap" && result(current: false, expected: true, taps: 1) == "tap" && result(current: false, expected: true, taps: 2) == "fail"),
    ("desired-false-missed-first-then-success", result(current: true, expected: false, taps: 0) == "tap" && result(current: true, expected: false, taps: 1) == "tap" && result(current: false, expected: false, taps: 2) == "succeed"),
    ("desired-false-persistent-mismatch", result(current: true, expected: false, taps: 0) == "tap" && result(current: true, expected: false, taps: 1) == "tap" && result(current: true, expected: false, taps: 2) == "fail"),
    ("already-desired-no-tap", result(current: true, expected: true, taps: 0) == "succeed" && result(current: false, expected: false, taps: 1) == "succeed"),
    ("unreadable-no-tap", result(current: nil, expected: true, taps: 0) == "fail" && result(current: nil, expected: false, taps: 2) == "fail")
]
for (name, passed) in checks {
    print("\(name): \(passed ? "pass" : "fail")")
    precondition(passed, "Unexpected action for \(name)")
}
