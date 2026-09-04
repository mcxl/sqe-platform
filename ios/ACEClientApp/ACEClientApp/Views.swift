import Foundation
import SwiftUI
import UIKit

struct RootView: View {
    @ObservedObject var state: SessionState

    var body: some View {
        #if DEBUG
        if let scenario = UITestScenario.current { ScenarioRootView(scenario: scenario) }
        else { content }
        #else
        content
        #endif
    }

    @ViewBuilder private var content: some View {
        let presentation = state.screen.presentation
        Group {
            switch presentation {
            case .configuration(let message):
                SafeMessageView(message: message, action: nil)
            case .signIn(let message):
                SignInView(message: message, submit: state.signIn)
            case .loading:
                ProgressView("Loading")
                    .accessibilityLabel("Loading current release")
            case .release(let release, let notices):
                ReleaseView(release: release, notices: notices, refresh: state.refresh, signOut: state.signOut)
            case .empty(let message):
                CurrentReleaseMessageView(message: message, retry: .refresh, state: state)
            case .failure(let message, let retry):
                CurrentReleaseMessageView(message: message, retry: retry, state: state)
            case .deletionPending(let message, let deletionOnlyRecovery):
                SafeMessageView(message: message, action: (deletionOnlyRecovery ? "Reset saved sign-in" : "Try again", deletionOnlyRecovery ? state.resetSavedSignIn : { state.retry(.deletion) }))
            }
        }
        .padding()
        .modifier(ErrorAnnouncement(message: presentation.errorMessage, event: state.errorAnnouncementEvent))
    }
}

private struct ErrorAnnouncement: ViewModifier {
    let message: String?
    let event: Int

    func body(content: Content) -> some View {
        content
            .onAppear { announce(message) }
            .onChange(of: event) { _, _ in announce(message) }
    }

    private func announce(_ message: String?) {
        guard let message else { return }
        UIAccessibility.post(notification: .announcement, argument: message as NSString)
    }
}

struct SignInView: View {
    let message: String?
    let submit: (String, String) -> Void
    @State private var username = ""
    @State private var password = ""

    var body: some View {
        Form {
            Section("Sign In") {
                TextField("Username", text: $username)
                    .textInputAutocapitalization(.never)
                    .accessibilityLabel("Username")
                SecureField("Password", text: $password)
                    .textInputAutocapitalization(.never)
                    .accessibilityLabel("Password")
                if let message { Text(message) }
                Button("Sign in") {
                    let enteredUsername = username
                    let enteredPassword = password
                    username = ""
                    password = ""
                    submit(enteredUsername, enteredPassword)
                }
                .accessibilityLabel("Sign in")
            }
        }
    }
}

struct CurrentReleaseMessageView: View {
    let message: String
    let retry: RetryAction
    @ObservedObject var state: SessionState

    var body: some View {
        VStack(spacing: 20) {
            HandlingLabel()
            Text(message).multilineTextAlignment(.center)
            Button(retry == .keychainRead ? "Try again" : "Refresh") { state.retry(retry) }
                .accessibilityLabel(retry == .keychainRead ? "Retry saved sign-in read" : "Refresh current release")
            if retry == .refresh { Button("Sign out") { state.signOut() }.accessibilityLabel("Sign out") }
        }
    }
}

struct SafeMessageView: View {
    let message: String
    let action: (String, () -> Void)?
    var body: some View {
        VStack(spacing: 20) {
            Text(message).multilineTextAlignment(.center)
            if let action { Button(action.0, action: action.1).accessibilityLabel(action.0) }
        }
    }
}

struct ReleaseView: View {
    let release: ClientReleaseResponse
    let notices: [String]
    let refresh: () -> Void
    let signOut: () -> Void

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                HandlingLabel()
                ValueRow(field: .engagementName, value: release.engagementName)
                ValueRow(field: .reviewStatus, value: release.reviewStatus)
                ValueRow(field: .releaseVersion, value: String(release.releaseVersion))
                ValueRow(field: .publishedAt, value: release.publishedAt)
                if let conclusion = release.conclusion {
                    SectionHeader("Conclusion")
                    ValueRow(field: .conclusionTitle, value: conclusion.title)
                    ValueRow(field: .conclusionSummary, value: conclusion.summary)
                    ValueRow(field: .evidenceReference, value: conclusion.evidenceReferenceID)
                }
                if !release.actions.isEmpty {
                    SectionHeader("Actions")
                    ForEach(Array(release.actions.enumerated()), id: \.offset) { index, action in
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Action \(index + 1)").font(.headline)
                            ValueRow(field: .actionDescription, value: action.description)
                            ValueRow(field: .actionOwner, value: action.owner)
                            ValueRow(field: .actionTargetDate, value: action.targetDate)
                            ValueRow(field: .actionStatus, value: action.status)
                        }
                        .accessibilityElement(children: .contain)
                    }
                }
                ForEach(notices, id: \.self) { notice in Text(notice) }
                Button("Refresh", action: refresh).accessibilityLabel("Refresh current release")
                Button("Sign out", action: signOut).accessibilityLabel("Sign out")
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }
}

struct SectionHeader: View {
    let value: String
    init(_ value: String) { self.value = value }
    var body: some View { Text(value).font(.title3.bold()).accessibilityAddTraits(.isHeader) }
}

enum CopyableReleaseField: CaseIterable {
    case engagementName, reviewStatus, releaseVersion, publishedAt, conclusionTitle, conclusionSummary, evidenceReference, actionDescription, actionOwner, actionTargetDate, actionStatus
    var label: String {
        switch self {
        case .engagementName: return "Engagement name"
        case .reviewStatus: return "Review status"
        case .releaseVersion: return "Release version"
        case .publishedAt: return "Published date and time"
        case .conclusionTitle: return "Conclusion title"
        case .conclusionSummary: return "Conclusion summary"
        case .evidenceReference: return "Evidence reference"
        case .actionDescription: return "Action description"
        case .actionOwner: return "Action owner"
        case .actionTargetDate: return "Action target date"
        case .actionStatus: return "Action status"
        }
    }
}

struct ValueRow: View {
    let field: CopyableReleaseField
    let value: String
    @State private var confirmation: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(field.label).font(.headline)
            Text(value).textSelection(.enabled).accessibilityLabel("\(field.label): \(value)")
            Button("Copy \(field.label)") {
                ClipboardWriteContract.write(visibleValue: value, writtenAt: Date())
                let announcement = "Copied \(field.label)."
                confirmation = announcement
                UIAccessibility.post(notification: .announcement, argument: announcement as NSString)
            }
            .accessibilityLabel("Copy \(field.label)")
            if let confirmation { Text(confirmation) }
        }
    }
}

enum ClipboardWriteContract {
    static func item(visibleValue: String) -> [String: Any] {
        ["public.utf8-plain-text": visibleValue]
    }

    static func options(writtenAt: Date) -> [UIPasteboard.OptionsKey: Any] {
        [.localOnly: true, .expirationDate: writtenAt.addingTimeInterval(300)]
    }

    static func write(visibleValue: String, writtenAt: Date, pasteboard: UIPasteboard = .general) {
        pasteboard.setItems([item(visibleValue: visibleValue)], options: options(writtenAt: writtenAt))
    }
}

struct HandlingLabel: View {
    var body: some View {
        Text("FICTIONAL PILOT — CONTROLLED")
            .font(.footnote.bold())
            .accessibilityLabel("FICTIONAL PILOT — CONTROLLED")
    }
}

struct PrivacyCoverView: View {
    var body: some View {
        VStack(spacing: 12) {
            Text("ACE Client")
            Text("FICTIONAL PILOT — CONTROLLED")
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(uiColor: .systemBackground))
    }
}
