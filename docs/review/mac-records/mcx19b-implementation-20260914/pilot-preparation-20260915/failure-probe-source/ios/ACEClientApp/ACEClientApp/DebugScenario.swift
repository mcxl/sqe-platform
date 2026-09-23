#if DEBUG
import SwiftUI

enum UITestScenario: String {
    case configuration, signIn, loading, emptyRelease, emptyEngagement, release, noConclusion, noActions
    case denied, unavailable, unexpected, connection, timeout, invalidResponse, secure
    case keychainRead, keychainWrite, keychainDeletion, deletionOnly, deletionRetry, copyConfirmation, multiAction, privacy

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
        case .loading: ProgressView("Loading").accessibilityLabel("Loading current release")
        case .emptyRelease, .emptyEngagement: CurrentReleaseMessageView(message: "No current release is available.", retry: .refresh, retryAction: {}, signOutAction: {})
        case .denied: SignInView(message: "Access denied. Sign in again.", submit: { _, _ in })
        case .unavailable: CurrentReleaseMessageView(message: "ACE is unavailable. Try again later.", retry: .refresh, retryAction: {}, signOutAction: {})
        case .unexpected: CurrentReleaseMessageView(message: "ACE is unavailable. Try again later.", retry: .refresh, retryAction: {}, signOutAction: {})
        case .connection: CurrentReleaseMessageView(message: "ACE could not be reached. Check your connection and try again.", retry: .refresh, retryAction: {}, signOutAction: {})
        case .timeout: CurrentReleaseMessageView(message: "The request timed out. Try again.", retry: .refresh, retryAction: {}, signOutAction: {})
        case .invalidResponse: CurrentReleaseMessageView(message: "ACE is unavailable. Try again later.", retry: .refresh, retryAction: {}, signOutAction: {})
        case .secure: CurrentReleaseMessageView(message: "ACE could not establish a secure connection. Try again later.", retry: .refresh, retryAction: {}, signOutAction: {})
        case .keychainRead: CurrentReleaseMessageView(message: "Saved sign-in could not be read. Try again.", retry: .keychainRead, retryAction: {}, signOutAction: nil)
        case .keychainWrite: SignInView(message: "Sign-in could not be saved. Try again.", submit: { _, _ in })
        case .keychainDeletion: SafeMessageView(message: "Saved sign-in could not be removed. Try again.", action: ("Try again", {}))
        case .deletionOnly: SafeMessageView(message: "Saved sign-in must be reset before access.", action: ("Reset saved sign-in", {}))
        case .deletionRetry: SafeMessageView(message: "Sign-out could not be completed. Try again.", action: ("Try again", {}))
        case .release: ReleaseView(release: release, notices: [], refresh: {}, signOut: {})
        case .noConclusion:
            ReleaseView(release: ClientReleaseResponse(engagementName: release.engagementName, reviewStatus: release.reviewStatus, releaseVersion: release.releaseVersion, publishedAt: release.publishedAt, conclusion: nil, actions: release.actions), notices: ["No conclusion is available."], refresh: {}, signOut: {})
        case .noActions:
            ReleaseView(release: ClientReleaseResponse(engagementName: release.engagementName, reviewStatus: release.reviewStatus, releaseVersion: release.releaseVersion, publishedAt: release.publishedAt, conclusion: release.conclusion, actions: []), notices: ["No actions are available."], refresh: {}, signOut: {})
        case .copyConfirmation:
            ReleaseView(release: release, notices: [], refresh: {}, signOut: {})
        case .multiAction:
            MultiActionClipboardFixture(
                release: ClientReleaseResponse(
                    engagementName: release.engagementName,
                    reviewStatus: release.reviewStatus,
                    releaseVersion: release.releaseVersion,
                    publishedAt: release.publishedAt,
                    conclusion: release.conclusion,
                    actions: [
                        release.actions[0],
                        ClientAction(description: "Second fictional action", owner: "Second fictional owner", targetDate: "2026-08-26", status: "COMPLETE")
                    ]
                )
            )
        case .privacy: PrivacyCoverView()
        }
    }
}

private struct MultiActionClipboardFixture: View {
    let release: ClientReleaseResponse
    @State private var isClipboardTestDestinationPresented = false

    var body: some View {
        ReleaseView(release: release, notices: [], refresh: {}, signOut: {})
            .safeAreaInset(edge: .bottom) {
                Button {
                    isClipboardTestDestinationPresented = true
                } label: {
                    Text("Clipboard test destination")
                        .frame(minWidth: 44, minHeight: 44)
                        .contentShape(Rectangle())
                }
                .accessibilityLabel("Clipboard test destination")
            }
            .sheet(isPresented: $isClipboardTestDestinationPresented) {
                ClipboardPasteFixture {
                    isClipboardTestDestinationPresented = false
                }
            }
    }
}

private struct ClipboardPasteFixture: View {
    let close: () -> Void
    @State private var pastedValue = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            TextEditor(text: $pastedValue)
                .frame(minHeight: 120)
                .accessibilityLabel("Clipboard paste destination")
            Button(action: close) {
                Text("Close")
                    .frame(minWidth: 44, minHeight: 44)
                    .contentShape(Rectangle())
            }
            .accessibilityLabel("Close clipboard test destination")
        }
        .padding()
        .onAppear { pastedValue = "" }
    }
}
#endif
