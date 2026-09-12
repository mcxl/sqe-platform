import Foundation
import XCTest
import UIKit

final class LandmarksTrialUITests: XCTestCase {
    override func setUpWithError() throws {
        continueAfterFailure = false
    }

    @MainActor
    func testReleaseInformationAndCopyControls() throws {
        let app = XCUIApplication()
        app.launch()

        setOrientation(.portrait, in: app, name: "release-portrait")
        let fields = releaseFields
        roundTripToCurrentRelease(in: app)
        for (label, value) in fields {
            let valueElement = app.descendants(matching: .any)
                .matching(NSPredicate(format: "label == %@", "\(label): \(value)")).firstMatch
            scrollToElement(valueElement, in: app)
            require(valueElement.exists && valueElement.isHittable, in: app, name: "copy-\(label)-value", "Missing \(label): \(value)")
            let copyButton = app.buttons["Copy \(label)"]
            scrollToElement(copyButton, in: app)
            require(copyButton.exists && copyButton.isHittable, in: app, name: "copy-\(label)-control", "Missing copy control for \(label)")
            copyButton.tap()
            let confirmation = app.staticTexts["Copied \(label)."]
            require(confirmation.waitForExistence(timeout: 2), in: app, name: "copy-\(label)-confirmation", "Missing copied confirmation for \(label)")
        }
        attachScreenshot(app, name: "release-portrait-success")
        try audit(app, name: "release-portrait")
        launchLandscape(app, name: "release-landscape")
        assertValues(fields, in: app, scenario: "release-landscape")
        attachScreenshot(app, name: "release-landscape-success")
        try audit(app, name: "release-landscape")
    }

    @MainActor
    func testReleaseAuditDiagnostic() throws {
        let app = XCUIApplication()
        app.launch()
        setOrientation(.portrait, in: app, name: "audit-diagnostic-portrait")
        attachScreenshot(app, name: "audit-diagnostic-launch")
        let copyButton = app.buttons["Copy Action status"]
        scrollToFullyVisible(copyButton, in: app)
        guard requireFullyVisible(copyButton, in: app, name: "audit-diagnostic-copy", "Copy Action status was not fully visible") else {
            return
        }
        copyButton.tap()
        let confirmation = app.staticTexts["Copied Action status."]
        guard confirmation.waitForExistence(timeout: 2) else {
            attachFailureEvidence(app, name: "audit-diagnostic-confirmation")
            XCTFail("Copied Action status confirmation was unavailable")
            return
        }
        scrollToFullyVisible(confirmation, in: app)
        guard requireFullyVisible(confirmation, in: app, name: "audit-diagnostic-confirmation", "Copied Action status confirmation was not fully visible") else {
            return
        }
        guard requireFullyVisible(copyButton, in: app, name: "audit-diagnostic-copy-recheck", "Copy Action status was not fully visible after confirmation") else {
            return
        }
        attachAuditDiagnosticViewportEvidence(app, copyButton: copyButton, confirmation: confirmation)
        try audit(app, name: "audit-diagnostic-bottom")
    }

    @MainActor
    func testReleaseClipboardBridge() throws {
        let app = XCUIApplication()
        app.launch()

        setOrientation(.portrait, in: app, name: "clipboard-bridge-portrait")
        roundTripToCurrentRelease(in: app)
        for (index, (label, value)) in releaseFields.enumerated() {
            let valueElement = app.descendants(matching: .any)
                .matching(NSPredicate(format: "label == %@", "\(label): \(value)")).firstMatch
            scrollToElement(valueElement, in: app)
            require(valueElement.exists && valueElement.isHittable, in: app, name: "clipboard-bridge-\(label)-value", "Missing \(label): \(value)")
            let copyButton = app.buttons["Copy \(label)"]
            scrollToElement(copyButton, in: app)
            require(copyButton.exists && copyButton.isHittable, in: app, name: "clipboard-bridge-\(label)-control", "Missing copy control for \(label)")
            copyButton.tap()
            require(app.staticTexts["Copied \(label)."].waitForExistence(timeout: 2), in: app, name: "clipboard-bridge-\(label)-confirmation", "Missing copied confirmation for \(label)")
            emitClipboardBridgeMarker(index)
            Thread.sleep(forTimeInterval: 7)
        }
        attachScreenshot(app, name: "clipboard-bridge-success")
    }

    @MainActor
    func testReleaseLayoutAndAccessibility() throws {
        let app = XCUIApplication()
        app.launch()

        setOrientation(.portrait, in: app, name: "accessibility-portrait")
        try auditVisiblePages(releaseFields, in: app, scenario: "accessibility-portrait")
        launchLandscape(app, name: "accessibility-landscape")
        try auditVisiblePages(releaseFields, in: app, scenario: "accessibility-landscape")
    }

    @MainActor
    private func setOrientation(_ orientation: UIDeviceOrientation, in app: XCUIApplication, name: String) {
        XCUIDevice.shared.orientation = orientation
        require(app.navigationBars["Release Details"].waitForExistence(timeout: 10), in: app, name: "\(name)-launch", "Release detail did not load for \(name)")
        let frame = app.windows.firstMatch.frame
        let expected = orientation.isLandscape ? "width > height" : "width < height"
        let actual = "width=\(frame.width); height=\(frame.height)"
        let isExpectedAspect = orientation.isLandscape ? frame.width > frame.height : frame.width < frame.height
        require(isExpectedAspect, in: app, name: "\(name)-aspect", "Unexpected app window aspect for \(name): expected \(expected); actual \(actual)")
    }

    @MainActor
    private func launchLandscape(_ app: XCUIApplication, name: String) {
        XCUIDevice.shared.orientation = .landscapeLeft
        app.terminate()
        app.launch()
        setOrientation(.landscapeLeft, in: app, name: name)
    }

    @MainActor
    private func audit(_ app: XCUIApplication, name: String) throws {
        attachScreenshot(app, name: name)
        let diagnostic = XCTAttachment(string: "orientation=\(XCUIDevice.shared.orientation.rawValue); frame=\(app.windows.firstMatch.frame)")
        diagnostic.name = "\(name)-traits"
        diagnostic.lifetime = .keepAlways
        add(diagnostic)
        do {
            try app.performAccessibilityAudit(for: .all) { issue in
                let issueText = "type=\(issue.auditType.rawValue)\nsummary=\(issue.compactDescription)\ndetails=\(issue.detailedDescription)\nelement=\(issue.element?.debugDescription ?? "unavailable")"
                print("ACE_AUDIT_ISSUE \(issueText)")
                let details = XCTAttachment(string: issueText)
                details.name = "\(name)-audit-issue"
                details.lifetime = .keepAlways
                self.add(details)
                self.attachFailureEvidence(app, name: "\(name)-audit-issue")
                return false
            }
        } catch {
            attachFailureEvidence(app, name: "\(name)-audit-failure")
            throw error
        }
    }

    @MainActor
    private func scrollToElement(_ element: XCUIElement, in app: XCUIApplication) {
        for _ in 0..<12 where !element.exists || !element.isHittable {
            app.swipeUp()
        }
    }

    @MainActor
    private func scrollToFullyVisible(_ element: XCUIElement, in app: XCUIApplication) {
        for _ in 0..<8 {
            let viewport = auditDiagnosticViewport(in: app)
            if isFullyVisible(element, in: viewport) {
                return
            }
            let frame = element.exists ? element.frame : .null
            if hasUsableFrame(frame) && hasUsableFrame(viewport.visible) && frame.minY < viewport.visible.minY {
                app.swipeDown()
            } else {
                app.swipeUp()
            }
        }
    }

    @MainActor
    private func requireFullyVisible(_ element: XCUIElement, in app: XCUIApplication, name: String, _ message: String) -> Bool {
        let viewport = auditDiagnosticViewport(in: app)
        guard isFullyVisible(element, in: viewport) else {
            attachFailureEvidence(app, name: name)
            XCTFail("\(message). \(auditDiagnosticFrameRecord(viewport, element: element))")
            return false
        }
        return true
    }

    @MainActor
    private func attachAuditDiagnosticViewportEvidence(_ app: XCUIApplication, copyButton: XCUIElement, confirmation: XCUIElement) {
        let viewport = auditDiagnosticViewport(in: app)
        let record = auditDiagnosticFrameRecord(viewport, element: copyButton) + "\nconfirmation=\(confirmation.frame)"
        let diagnostic = XCTAttachment(string: record)
        diagnostic.name = "audit-diagnostic-viewport-frames"
        diagnostic.lifetime = .keepAlways
        add(diagnostic)
        attachScreenshot(app, name: "audit-diagnostic-viewport")
        let hierarchy = XCTAttachment(string: app.debugDescription)
        hierarchy.name = "audit-diagnostic-viewport-hierarchy"
        hierarchy.lifetime = .keepAlways
        add(hierarchy)
    }

    @MainActor
    private func auditDiagnosticViewport(in app: XCUIApplication) -> (window: CGRect, navigationBar: CGRect, list: CGRect, visible: CGRect) {
        let window = app.windows.firstMatch.frame
        let navigationBar = app.navigationBars["Release Details"].frame
        let list = app.collectionViews.firstMatch.frame
        let intersection = window.intersection(list)
        let top = max(intersection.minY, navigationBar.maxY)
        let visible = top < intersection.maxY
            ? CGRect(x: intersection.minX, y: top, width: intersection.width, height: intersection.maxY - top)
            : .null
        return (window, navigationBar, list, visible)
    }

    @MainActor
    private func isFullyVisible(_ element: XCUIElement, in viewport: (window: CGRect, navigationBar: CGRect, list: CGRect, visible: CGRect)) -> Bool {
        guard element.exists else { return false }
        let frame = element.frame
        return element.isHittable
            && hasUsableFrame(viewport.window)
            && hasUsableFrame(viewport.navigationBar)
            && hasUsableFrame(viewport.list)
            && hasUsableFrame(viewport.visible)
            && hasUsableFrame(frame)
            && viewport.visible.contains(frame)
            && !frame.intersects(viewport.navigationBar)
    }

    private func hasUsableFrame(_ frame: CGRect) -> Bool {
        !frame.isNull && !frame.isInfinite && !frame.isEmpty && frame.width > 0 && frame.height > 0
    }

    @MainActor
    private func auditDiagnosticFrameRecord(_ viewport: (window: CGRect, navigationBar: CGRect, list: CGRect, visible: CGRect), element: XCUIElement) -> String {
        let frame = element.exists ? element.frame : .null
        return "window=\(viewport.window)\nnavigationBar=\(viewport.navigationBar)\nlist=\(viewport.list)\nvisible=\(viewport.visible)\nelementExists=\(element.exists)\nelement=\(frame)"
    }

    @MainActor
    private func assertValues(_ fields: [(String, String)], in app: XCUIApplication, scenario: String) {
        for (label, value) in fields {
            let valueElement = app.descendants(matching: .any)
                .matching(NSPredicate(format: "label == %@", "\(label): \(value)")).firstMatch
            scrollToElement(valueElement, in: app)
            require(valueElement.exists && valueElement.isHittable, in: app, name: "\(scenario)-\(label)", "Missing \(label): \(value)")
        }
    }

    @MainActor
    private func auditVisiblePages(_ fields: [(String, String)], in app: XCUIApplication, scenario: String) throws {
        let matrixStarted = Date()
        var auditedSignatures = Set<String>()
        var auditCount = 0
        for (label, value) in fields {
            let valueElement = app.descendants(matching: .any)
                .matching(NSPredicate(format: "label == %@", "\(label): \(value)")).firstMatch
            scrollToFullyVisible(valueElement, in: app)
            guard requireFullyVisible(valueElement, in: app, name: "\(scenario)-\(label)", "\(label): \(value) was not fully visible") else {
                return
            }
            let signature = matrixViewportSignature(fields, in: app)
            let isNewViewport = auditedSignatures.insert(signature).inserted
            attachMatrixRowEvidence(
                app,
                label: label,
                value: value,
                element: valueElement,
                scenario: scenario,
                signature: signature,
                auditState: isNewViewport ? "scheduled" : "already-covered"
            )
            guard isNewViewport else {
                continue
            }
            auditCount += 1
            let auditName = "\(scenario)-viewport-\(auditCount)"
            attachMatrixAuditEvidence(
                app,
                fields: fields,
                scenario: scenario,
                signature: signature,
                auditName: auditName,
                auditCount: auditCount
            )
            do {
                let auditStarted = Date()
                defer {
                    attachMatrixAuditDuration(
                        scenario: scenario,
                        auditName: auditName,
                        seconds: Date().timeIntervalSince(auditStarted)
                    )
                }
                try audit(app, name: auditName)
            }
        }
        attachMatrixAuditDuration(
            scenario: scenario,
            auditName: "\(scenario)-summary",
            seconds: Date().timeIntervalSince(matrixStarted),
            auditCount: auditCount
        )
    }

    @MainActor
    private func matrixViewportSignature(_ fields: [(String, String)], in app: XCUIApplication) -> String {
        let viewport = auditDiagnosticViewport(in: app)
        let rows = fields.enumerated().map { index, field in
            let element = app.descendants(matching: .any)
                .matching(NSPredicate(format: "label == %@", "\(field.0): \(field.1)")).firstMatch
            let exists = element.exists
            let frame = exists ? element.frame : .null
            return "\(index):exists=\(exists);frame=\(frame)"
        }
        return "window=\(viewport.window);navigationBar=\(viewport.navigationBar);list=\(viewport.list);visible=\(viewport.visible);rows=\(rows.joined(separator: "|"))"
    }

    @MainActor
    private func attachMatrixRowEvidence(_ app: XCUIApplication, label: String, value: String, element: XCUIElement, scenario: String, signature: String, auditState: String) {
        let viewport = auditDiagnosticViewport(in: app)
        let exists = element.exists
        let frame = exists ? element.frame : .null
        let record = "scenario=\(scenario)\norientation=\(XCUIDevice.shared.orientation.rawValue)\nlabel=\(label)\nvalue=\(value)\nelementExists=\(exists)\nelementFrame=\(frame)\nwindow=\(viewport.window)\nnavigationBar=\(viewport.navigationBar)\nlist=\(viewport.list)\nvisible=\(viewport.visible)\nauditState=\(auditState)\nviewportSignature=\(signature)"
        let attachment = XCTAttachment(string: record)
        attachment.name = "\(scenario)-\(label)-row"
        attachment.lifetime = .keepAlways
        add(attachment)
    }

    @MainActor
    private func attachMatrixAuditEvidence(_ app: XCUIApplication, fields: [(String, String)], scenario: String, signature: String, auditName: String, auditCount: Int) {
        let viewport = auditDiagnosticViewport(in: app)
        let coveredRows = fields.compactMap { label, value -> String? in
            let element = app.descendants(matching: .any)
                .matching(NSPredicate(format: "label == %@", "\(label): \(value)")).firstMatch
            return isFullyVisible(element, in: viewport) ? "\(label): \(value)" : nil
        }
        let record = "scenario=\(scenario)\nauditName=\(auditName)\nauditCount=\(auditCount)\norientation=\(XCUIDevice.shared.orientation.rawValue)\ncoveredRows=\(coveredRows.joined(separator: " | "))\nwindow=\(viewport.window)\nnavigationBar=\(viewport.navigationBar)\nlist=\(viewport.list)\nvisible=\(viewport.visible)\nviewportSignature=\(signature)"
        let attachment = XCTAttachment(string: record)
        attachment.name = "\(auditName)-coverage"
        attachment.lifetime = .keepAlways
        add(attachment)
    }

    @MainActor
    private func attachMatrixAuditDuration(scenario: String, auditName: String, seconds: TimeInterval, auditCount: Int? = nil) {
        let formattedSeconds = String(format: "%.3f", seconds)
        var record = "scenario=\(scenario)\nauditName=\(auditName)\ndurationSeconds=\(formattedSeconds)"
        if let auditCount {
            record += "\nauditCount=\(auditCount)"
        }
        let attachment = XCTAttachment(string: record)
        attachment.name = "\(auditName)-duration"
        attachment.lifetime = .keepAlways
        add(attachment)
    }

    @MainActor
    private func attachFailureEvidence(_ app: XCUIApplication, name: String) {
        attachScreenshot(app, name: name)
        let hierarchy = XCTAttachment(string: app.debugDescription)
        hierarchy.name = "\(name)-hierarchy"
        hierarchy.lifetime = .keepAlways
        add(hierarchy)
    }

    @MainActor
    private func roundTripToCurrentRelease(in app: XCUIApplication) {
        let navigationButtons = app.navigationBars.buttons
        let sidebarButton = navigationButtons["Show Sidebar"].firstMatch
        let navigationButton = sidebarButton.exists ? sidebarButton : navigationButtons.firstMatch
        require(navigationButton.exists && navigationButton.isHittable, in: app, name: "release-sidebar-control", "The sidebar navigation control was unavailable")
        navigationButton.tap()
        let currentRelease = app.staticTexts["Current Release"].firstMatch
        require(currentRelease.waitForExistence(timeout: 10), in: app, name: "release-sidebar-row", "Current Release was unavailable in the sidebar")
        currentRelease.tap()
        require(app.navigationBars["Release Details"].waitForExistence(timeout: 10), in: app, name: "release-detail-return", "Release Details did not return from the sidebar")
    }

    @MainActor
    private func attachScreenshot(_ app: XCUIApplication, name: String) {
        let screenshot = XCTAttachment(screenshot: app.screenshot())
        screenshot.name = name
        screenshot.lifetime = .keepAlways
        add(screenshot)
    }

    @MainActor
    private func emitClipboardBridgeMarker(_ index: Int) {
        let marker = "ACE_CLIPBOARD_BRIDGE_MARKER index=\(index)\n"
        FileHandle.standardOutput.write(Data(marker.utf8))
    }

    @MainActor
    private func require(_ condition: @autoclosure () -> Bool, in app: XCUIApplication, name: String, _ message: String) {
        guard condition() else {
            attachFailureEvidence(app, name: name)
            XCTFail(message)
            return
        }
    }

    private let releaseFields = [
        ("Engagement name", "Fictional Engagement"),
        ("Review status", "RELEASED"),
        ("Release version", "1"),
        ("Published date and time", "2026-08-24T10:15:30Z"),
        ("Conclusion title", "Fictional conclusion"),
        ("Conclusion summary", "Fictional summary"),
        ("Evidence reference", "FICTIONAL-REF-001"),
        ("Action description", "Fictional action"),
        ("Action owner", "Fictional owner"),
        ("Action target date", "2026-08-25"),
        ("Action status", "OPEN")
    ]
}
