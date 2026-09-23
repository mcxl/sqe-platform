#if DEBUG
import SwiftUI

enum UITestScenario: String {
    case configuration, signIn, loading, emptyRelease, emptyEngagement, release, noConclusion, noActions
    case denied, unavailable, unexpected, connection, timeout, invalidResponse, secure
    case keychainRead, keychainWrite, keychainDeletion, deletionOnly, deletionRetry, copyConfirmation, privacy

    static var current: UITestScenario? {
        guard let raw = ProcessInfo.processInfo.environment["ACE_UI_TEST_SCENARIO"] else { return nil }
        return UITestScenario(rawValue: raw)
    }
}

struct ScenarioRootView: View {
    let scenario: UITestScenario
    private let release = ClientReleaseResponse(
        engagementName: "Fictional Engagement", reviewStatus: "RELEASED", releaseVersion: 1,
        publishedAt: "2026-08-24T10:15:30Z",
        conclusion: ClientConclusion(title: "Fictional conclusion", summary: "Fictional summary", evidenceReferenceID: "FICTIONAL-REF-001"),
        actions: [ClientAction(description: "Fictional action", owner: "Fictional owner", targetDate: "2026-08-25", status: "OPEN")]
    )

    var body: some View {
        switch scenario {
        case .configuration: SafeMessageView(message: "This app is not configured for access.", action: nil)
        case .signIn: SignInView(message: nil, submit: { _, _ in })
        case .loading: ProgressView("Loading")
        case .emptyRelease, .emptyEngagement: SafeMessageView(message: "No current release is available.", action: ("Refresh", {}))
        case .denied: SafeMessageView(message: "Access denied. Sign in again.", action: nil)
        case .unavailable: SafeMessageView(message: "ACE is unavailable. Try again later.", action: ("Refresh", {}))
        case .unexpected: SafeMessageView(message: "ACE is unavailable. Try again later.", action: ("Refresh", {}))
        case .connection: SafeMessageView(message: "ACE could not be reached. Check your connection and try again.", action: ("Refresh", {}))
        case .timeout: SafeMessageView(message: "The request timed out. Try again.", action: ("Refresh", {}))
        case .invalidResponse: SafeMessageView(message: "ACE is unavailable. Try again later.", action: ("Refresh", {}))
        case .secure: SafeMessageView(message: "ACE could not establish a secure connection. Try again later.", action: ("Refresh", {}))
        case .keychainRead: SafeMessageView(message: "Saved sign-in could not be read. Try again.", action: ("Try again", {}))
        case .keychainWrite: SafeMessageView(message: "Sign-in could not be saved. Try again.", action: nil)
        case .keychainDeletion: SafeMessageView(message: "Saved sign-in could not be removed. Try again.", action: ("Try again", {}))
        case .deletionOnly: SafeMessageView(message: "Saved sign-in must be reset before access.", action: ("Reset saved sign-in", {}))
        case .deletionRetry: SafeMessageView(message: "Sign-out could not be completed. Try again.", action: ("Try again", {}))
        case .release: ReleaseView(release: release, notices: [], refresh: {}, signOut: {})
        case .noConclusion:
            ReleaseView(release: ClientReleaseResponse(engagementName: release.engagementName, reviewStatus: release.reviewStatus, releaseVersion: release.releaseVersion, publishedAt: release.publishedAt, conclusion: nil, actions: release.actions), notices: ["No conclusion is available."], refresh: {}, signOut: {})
        case .noActions:
            ReleaseView(release: ClientReleaseResponse(engagementName: release.engagementName, reviewStatus: release.reviewStatus, releaseVersion: release.releaseVersion, publishedAt: release.publishedAt, conclusion: release.conclusion, actions: []), notices: ["No actions are available."], refresh: {}, signOut: {})
        case .copyConfirmation: ValueRow(field: .engagementName, value: release.engagementName)
        case .privacy: PrivacyCoverView()
        }
    }
}
#endif
