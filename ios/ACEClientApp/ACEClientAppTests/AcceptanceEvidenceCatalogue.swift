import Foundation
import XCTest

/// One entry exists for each approved acceptance identifier. Runtime-only entries
/// remain pending until an approved macOS, Xcode, simulator, and device are available.
struct AcceptanceEvidenceEntry: Sendable, Equatable {
    let identifier: String
    let test: String

    init(identifier: String, test: String) {
        self.identifier = identifier
        self.test = "test" + test.prefix(1).uppercased() + String(test.dropFirst())
    }
}

enum AcceptanceEvidenceCatalogue {
    static let entries: [AcceptanceEvidenceEntry] = [
        .init(identifier: "IOS-BASE-001", test: "projectConfiguration"),
        .init(identifier: "IOS-BASE-002", test: "projectConfiguration"),
        .init(identifier: "IOS-BASE-003", test: "projectConfiguration"),
        .init(identifier: "IOS-BASE-004", test: "projectConfiguration"),
        .init(identifier: "IOS-BASE-005", test: "sourceBoundaryInspection"),
        .init(identifier: "IOS-BASE-006", test: "sourceBoundaryInspection"),
        .init(identifier: "IOS-MODEL-001", test: "releaseValidation"),
        .init(identifier: "IOS-MODEL-002", test: "releaseValidation"),
        .init(identifier: "IOS-MODEL-003", test: "decodingFailsClosed"),
        .init(identifier: "IOS-MODEL-004", test: "decodingFailsClosed"),
        .init(identifier: "IOS-MODEL-005", test: "decodingFailsClosed"),
        .init(identifier: "IOS-MODEL-006", test: "releaseValidation"),
        .init(identifier: "IOS-MODEL-007", test: "releaseValidation"),
        .init(identifier: "IOS-MODEL-008", test: "releaseValidation"),
        .init(identifier: "IOS-MODEL-009", test: "decodingFailsClosed"),
        .init(identifier: "IOS-MODEL-010", test: "releaseValidation"),
        .init(identifier: "IOS-MODEL-011", test: "decodingFailsClosed"),
        .init(identifier: "IOS-MODEL-012", test: "decodingFailsClosed"),
        .init(identifier: "IOS-MODEL-013", test: "releaseValidation"),
        .init(identifier: "IOS-MODEL-014", test: "releaseValidation"),
        .init(identifier: "IOS-MODEL-015", test: "releaseValidation"),
        .init(identifier: "IOS-MODEL-016", test: "releaseValidation"),
        .init(identifier: "IOS-MODEL-017", test: "stateMatrix"),
        .init(identifier: "IOS-MODEL-018", test: "stateMatrix"),
        .init(identifier: "IOS-NET-001", test: "requestConstruction"),
        .init(identifier: "IOS-NET-002", test: "requestConstruction"),
        .init(identifier: "IOS-NET-003", test: "requestConstruction"),
        .init(identifier: "IOS-NET-004", test: "originValidation"),
        .init(identifier: "IOS-NET-005", test: "redirectDelegate"),
        .init(identifier: "IOS-NET-006", test: "redirectDelegate"),
        .init(identifier: "IOS-NET-007", test: "trustHandlingSourceInspection"),
        .init(identifier: "IOS-NET-008", test: "trustHandlingSourceInspection"),
        .init(identifier: "IOS-NET-009", test: "repositoryResponseMapping"),
        .init(identifier: "IOS-NET-010", test: "stateGeneration"),
        .init(identifier: "IOS-NET-011", test: "stateGeneration"),
        .init(identifier: "IOS-NET-012", test: "repositoryResponseMapping"),
        .init(identifier: "IOS-NET-013", test: "repositoryResponseMapping"),
        .init(identifier: "IOS-NET-014", test: "requestConstruction"),
        .init(identifier: "IOS-NET-015", test: "originValidation"),
        .init(identifier: "IOS-NET-016", test: "originValidation"),
        .init(identifier: "IOS-NET-017", test: "sessionConfiguration"),
        .init(identifier: "IOS-NET-018", test: "sessionConfiguration"),
        .init(identifier: "IOS-NET-019", test: "sessionConfiguration"),
        .init(identifier: "IOS-NET-020", test: "sessionConfiguration"),
        .init(identifier: "IOS-NET-021", test: "redirectDelegate"),
        .init(identifier: "IOS-NET-022", test: "redirectDelegate"),
        .init(identifier: "IOS-NET-023", test: "redirectDelegate"),
        .init(identifier: "IOS-NET-024", test: "redirectDelegate"),
        .init(identifier: "IOS-NET-025", test: "redirectDelegate"),
        .init(identifier: "IOS-NET-026", test: "repositoryResponseMapping"),
        .init(identifier: "IOS-NET-027", test: "originValidation"),
        .init(identifier: "IOS-NET-028", test: "trustHandlingSourceInspection"),
        .init(identifier: "IOS-NET-029", test: "projectConfiguration"),
        .init(identifier: "IOS-NET-030", test: "trustHandlingSourceInspection"),
        .init(identifier: "IOS-AUTH-001", test: "keychainLifecycle"),
        .init(identifier: "IOS-AUTH-002", test: "keychainLifecycle"),
        .init(identifier: "IOS-AUTH-003", test: "keychainLifecycle"),
        .init(identifier: "IOS-AUTH-004", test: "keychainQueries"),
        .init(identifier: "IOS-AUTH-005", test: "stateErrorHandling"),
        .init(identifier: "IOS-AUTH-006", test: "privacySourceInspection"),
        .init(identifier: "IOS-AUTH-007", test: "privacySourceInspection"),
        .init(identifier: "IOS-AUTH-008", test: "sessionConfiguration"),
        .init(identifier: "IOS-AUTH-009", test: "stateGeneration"),
        .init(identifier: "IOS-AUTH-010", test: "stateGeneration"),
        .init(identifier: "IOS-AUTH-011", test: "keychainQueries"),
        .init(identifier: "IOS-AUTH-012", test: "keychainQueries"),
        .init(identifier: "IOS-AUTH-013", test: "keychainQueries"),
        .init(identifier: "IOS-AUTH-014", test: "keychainQueries"),
        .init(identifier: "IOS-AUTH-015", test: "keychainLifecycle"),
        .init(identifier: "IOS-AUTH-016", test: "keychainQueries"),
        .init(identifier: "IOS-AUTH-017", test: "keychainLifecycle"),
        .init(identifier: "IOS-AUTH-018", test: "stateErrorHandling"),
        .init(identifier: "IOS-AUTH-019", test: "stateErrorHandling"),
        .init(identifier: "IOS-AUTH-020", test: "stateErrorHandling"),
        .init(identifier: "IOS-AUTH-021", test: "stateErrorHandling"),
        .init(identifier: "IOS-AUTH-022", test: "stateErrorHandling"),
        .init(identifier: "IOS-AUTH-023", test: "physicalDevicePending"),
        .init(identifier: "IOS-AUTH-024", test: "keychainLifecycle"),
        .init(identifier: "IOS-AUTH-025", test: "keychainLifecycle"),
        .init(identifier: "IOS-AUTH-026", test: "keychainValidation"),
        .init(identifier: "IOS-AUTH-027", test: "keychainLifecycle"),
        .init(identifier: "IOS-AUTH-028", test: "keychainLifecycle"),
        .init(identifier: "IOS-AUTH-029", test: "keychainSerialisation"),
        .init(identifier: "IOS-AUTH-030", test: "keychainQueries"),
        .init(identifier: "IOS-AUTH-031", test: "signInUITest"),
        .init(identifier: "IOS-AUTH-032", test: "signInUITest"),
        .init(identifier: "IOS-AUTH-033", test: "signInUITest"),
        .init(identifier: "IOS-AUTH-034", test: "safeInterfaceUITest"),
        .init(identifier: "IOS-AUTH-035", test: "safeInterfaceUITest"),
        .init(identifier: "IOS-AUTH-036", test: "evidencePrivacyInspection"),
        .init(identifier: "IOS-AUTH-037", test: "evidencePrivacyInspection"),
        .init(identifier: "IOS-AUTH-038", test: "keychainValidation"),
        .init(identifier: "IOS-AUTH-039", test: "keychainValidation"),
        .init(identifier: "IOS-AUTH-040", test: "keychainValidation"),
        .init(identifier: "IOS-AUTH-041", test: "keychainValidation"),
        .init(identifier: "IOS-AUTH-042", test: "keychainValidation"),
        .init(identifier: "IOS-AUTH-043", test: "keychainValidation"),
        .init(identifier: "IOS-AUTH-044", test: "keychainValidation"),
        .init(identifier: "IOS-AUTH-045", test: "keychainValidation"),
        .init(identifier: "IOS-AUTH-046", test: "keychainValidation"),
        .init(identifier: "IOS-AUTH-047", test: "keychainValidation"),
        .init(identifier: "IOS-AUTH-048", test: "keychainValidation"),
        .init(identifier: "IOS-AUTH-049", test: "keychainValidation"),
        .init(identifier: "IOS-AUTH-050", test: "keychainValidation"),
        .init(identifier: "IOS-AUTH-051", test: "keychainQueries"),
        .init(identifier: "IOS-AUTH-052", test: "keychainValidation"),
        .init(identifier: "IOS-AUTH-053", test: "keychainValidation"),
        .init(identifier: "IOS-AUTH-054", test: "keychainValidation"),
        .init(identifier: "IOS-AUTH-055", test: "keychainValidation"),
        .init(identifier: "IOS-AUTH-056", test: "keychainValidation"),
        .init(identifier: "IOS-AUTH-057", test: "stateErrorHandling"),
        .init(identifier: "IOS-AUTH-058", test: "stateErrorHandling"),
        .init(identifier: "IOS-AUTH-059", test: "stateErrorHandling"),
        .init(identifier: "IOS-AUTH-060", test: "stateErrorHandling"),
        .init(identifier: "IOS-AUTH-061", test: "keychainQueries"),
        .init(identifier: "IOS-AUTH-062", test: "stateErrorHandling"),
        .init(identifier: "IOS-AUTH-063", test: "stateErrorHandling"),
        .init(identifier: "IOS-AUTH-064", test: "keychainQueries"),
        .init(identifier: "IOS-AUTH-065", test: "keychainSourceInspection"),
        .init(identifier: "IOS-AUTH-066", test: "keychainValidation"),
        .init(identifier: "IOS-AUTH-067", test: "keychainValidation"),
        .init(identifier: "IOS-AUTH-068", test: "keychainValidation"),
        .init(identifier: "IOS-AUTH-069", test: "keychainValidation"),
        .init(identifier: "IOS-AUTH-070", test: "keychainValidation"),
        .init(identifier: "IOS-STATE-001", test: "releaseScreenUITest"),
        .init(identifier: "IOS-STATE-002", test: "stateErrorHandling"),
        .init(identifier: "IOS-STATE-003", test: "stateErrorHandling"),
        .init(identifier: "IOS-STATE-004", test: "stateErrorHandling"),
        .init(identifier: "IOS-STATE-005", test: "stateErrorHandling"),
        .init(identifier: "IOS-STATE-006", test: "stateErrorHandling"),
        .init(identifier: "IOS-STATE-007", test: "stateGeneration"),
        .init(identifier: "IOS-STATE-008", test: "stateErrorHandling"),
        .init(identifier: "IOS-STATE-009", test: "privacyCoverUITest"),
        .init(identifier: "IOS-STATE-010", test: "privacyCoverUITest"),
        .init(identifier: "IOS-STATE-011", test: "stateMatrix"),
        .init(identifier: "IOS-STATE-012", test: "stateMatrix"),
        .init(identifier: "IOS-STATE-013", test: "stateMatrix"),
        .init(identifier: "IOS-STATE-014", test: "stateMatrix"),
        .init(identifier: "IOS-STATE-015", test: "safeInterfaceUITest"),
        .init(identifier: "IOS-STATE-016", test: "stateErrorHandling"),
        .init(identifier: "IOS-STATE-017", test: "stateErrorHandling"),
        .init(identifier: "IOS-STATE-018", test: "stateErrorHandling"),
        .init(identifier: "IOS-COPY-001", test: "copyControlsUITest"),
        .init(identifier: "IOS-COPY-002", test: "clipboardContract"),
        .init(identifier: "IOS-COPY-003", test: "clipboardContract"),
        .init(identifier: "IOS-COPY-004", test: "copyControlsUITest"),
        .init(identifier: "IOS-COPY-005", test: "copyControlsUITest"),
        .init(identifier: "IOS-COPY-006", test: "copyControlsUITest"),
        .init(identifier: "IOS-COPY-007", test: "copyControlsUITest"),
        .init(identifier: "IOS-COPY-008", test: "clipboardContract"),
        .init(identifier: "IOS-COPY-009", test: "clipboardContract"),
        .init(identifier: "IOS-SHOT-001", test: "screenshotPolicyInspection"),
        .init(identifier: "IOS-SHOT-002", test: "screenshotPolicyInspection"),
        .init(identifier: "IOS-SHOT-003", test: "privacyCoverUITest"),
        .init(identifier: "IOS-SHOT-004", test: "sceneDelegateTest"),
        .init(identifier: "IOS-SHOT-005", test: "sceneDelegateTest"),
        .init(identifier: "IOS-SHOT-006", test: "sceneDelegateTest"),
        .init(identifier: "IOS-SHOT-007", test: "manualAppSwitcherPending"),
        .init(identifier: "IOS-SHOT-008", test: "sceneDelegateTest"),
        .init(identifier: "IOS-SHOT-009", test: "sceneDelegateTest"),
        .init(identifier: "IOS-SHOT-010", test: "signInUITest"),
        .init(identifier: "IOS-PRIV-001", test: "privacySourceInspection"),
        .init(identifier: "IOS-PRIV-002", test: "sessionConfiguration"),
        .init(identifier: "IOS-PRIV-003", test: "sessionConfiguration"),
        .init(identifier: "IOS-PRIV-004", test: "projectConfiguration"),
        .init(identifier: "IOS-PRIV-005", test: "projectConfiguration"),
        .init(identifier: "IOS-PRIV-006", test: "privacySourceInspection"),
        .init(identifier: "IOS-PRIV-007", test: "privacySourceInspection"),
        .init(identifier: "IOS-PRIV-008", test: "evidencePrivacyInspection"),
        .init(identifier: "IOS-PRIV-009", test: "sceneDelegateTest"),
        .init(identifier: "IOS-ACC-001", test: "voiceOverOrderUITest"),
        .init(identifier: "IOS-ACC-002", test: "accessibilityLabelsUITest"),
        .init(identifier: "IOS-ACC-003", test: "dynamicTypePending"),
        .init(identifier: "IOS-ACC-004", test: "boldTextPending"),
        .init(identifier: "IOS-ACC-005", test: "reduceMotionPending"),
        .init(identifier: "IOS-ACC-006", test: "contrastPending"),
        .init(identifier: "IOS-ACC-007", test: "layoutMatrixPending"),
        .init(identifier: "IOS-ACC-008", test: "accessibilityAuditPending"),
        .init(identifier: "IOS-ACC-009", test: "manualVoiceOverPending"),
        .init(identifier: "IOS-ACC-010", test: "simulatorMatrixPending"),
        .init(identifier: "IOS-ACC-011", test: "accessibilityAuditPending"),
        .init(identifier: "IOS-ACC-012", test: "dynamicTypePending"),
        .init(identifier: "IOS-ACC-013", test: "contrastPending"),
        .init(identifier: "IOS-ACC-014", test: "contrastPending"),
        .init(identifier: "IOS-ACC-015", test: "contrastPending"),
        .init(identifier: "IOS-ACC-016", test: "manualVoiceOverPending"),
        .init(identifier: "IOS-ACC-017", test: "manualVoiceOverPending"),
        .init(identifier: "IOS-ACC-018", test: "contrastPending"),
        .init(identifier: "IOS-ACC-019", test: "contrastPending"),
        .init(identifier: "IOS-BOUND-001", test: "requestConstruction"),
        .init(identifier: "IOS-BOUND-002", test: "sourceBoundaryInspection"),
        .init(identifier: "IOS-BOUND-003", test: "sourceBoundaryInspection"),
        .init(identifier: "IOS-BOUND-004", test: "sourceBoundaryInspection"),
        .init(identifier: "IOS-BOUND-005", test: "sourceBoundaryInspection"),
        .init(identifier: "IOS-BOUND-006", test: "serverCompatibilityExternal"),
        .init(identifier: "IOS-BOUND-007", test: "sourceBoundaryInspection"),
        .init(identifier: "IOS-BOUND-008", test: "fixtureInspection")
    ]
}

final class AcceptanceEvidenceCatalogueTests: XCTestCase {
    func testCatalogueHasUniqueIdentifiers() {
        XCTAssertEqual(AcceptanceEvidenceCatalogue.entries.count, 197)
        XCTAssertEqual(AcceptanceEvidenceCatalogue.entries.count, Set(AcceptanceEvidenceCatalogue.entries.map(\.identifier)).count)
    }

    func testCatalogueMethodsExist() throws {
        // ObjC runtime introspection (class_copyMethodList) is unavailable in
        // Swift 6 Release -O builds — non-@objc methods are not registered.
        // Validate catalogue entries against the contract tests source file
        // instead, which works at any optimization level.
        let sourceURL = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .appendingPathComponent("AcceptanceEvidenceContractTests.swift")
        let source = try String(contentsOf: sourceURL)

        let pattern = try NSRegularExpression(pattern: #"func (test\w+)\([^)]*\)"#)
        let range = NSRange(source.startIndex..., in: source)
        let methodNames = Set(
            pattern.matches(in: source, range: range).compactMap {
                Range($0.range(at: 1), in: source).map { String(source[$0]) }
            }
        )
        XCTAssertFalse(methodNames.isEmpty, "No test methods found in source")

        for entry in AcceptanceEvidenceCatalogue.entries {
            XCTAssertTrue(
                methodNames.contains(entry.test),
                "Catalogue '\(entry.identifier)' references '\(entry.test)' which is not a test method"
            )
        }
    }

    func testPendingRuntimePlanHasUniqueStructuredEntries() throws {
        let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
        let data = try Data(contentsOf: root.appendingPathComponent("RuntimeEvidencePlan.json"))
        let plan = try JSONDecoder().decode(RuntimePlan.self, from: data)
        let identifiers = plan.entries.flatMap(\.identifiers)
        XCTAssertEqual(identifiers.count, 44)
        XCTAssertEqual(identifiers.count, Set(identifiers).count)
        XCTAssertTrue(plan.entries.allSatisfy { !$0.identifiers.isEmpty && $0.status == "pending" && !$0.stage.isEmpty && !$0.device.isEmpty && !$0.procedure.isEmpty && !$0.expectedResult.isEmpty })
        let required = [runtimeID("BASE", 1), runtimeID("AUTH", 23), runtimeID("AUTH", 38), runtimeID("AUTH", 53), runtimeID("ACC", 1), runtimeID("NET", 7), runtimeID("NET", 15), runtimeID("NET", 16), runtimeID("SHOT", 1), runtimeID("SHOT", 7), runtimeID("SHOT", 10), runtimeID("BOUND", 6)]
        for identifier in required { XCTAssertEqual(identifiers.filter { $0 == identifier }.count, 1) }
    }

    private func runtimeID(_ family: String, _ number: Int) -> String { "IOS-\(family)-\(String(format: "%03d", number))" }
}
