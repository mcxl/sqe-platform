import Foundation

enum Probe {
    static let targetMeasurementPrecision: CGFloat = 0.000_000_001
    static func isAtLeast44Points(_ measurement: CGFloat) -> Bool {
        let minimum: CGFloat = 44
        // This test-harness precision policy does not model XCTest arithmetic.
        guard measurement.isFinite else { return false }
        return measurement >= minimum - Self.targetMeasurementPrecision
    }
}

let cases: [(String, CGFloat, Bool)] = [("44", 44, true), ("captured", 43.999999999999659, true), ("44-minus-0.5e-9", 44 - 0.5e-9, true), ("44-minus-2e-9", 44 - 2e-9, false), ("43.99", 43.99, false), ("zero", 0, false), ("negative", -1, false), ("NaN", .nan, false), ("positive-infinity", .infinity, false), ("negative-infinity", -.infinity, false)]
for (name, measurement, expected) in cases {
    let actual = Probe.isAtLeast44Points(measurement)
    print("\(name): \(actual) expected \(expected)")
    precondition(actual == expected, "Unexpected result for \(name)")
}
