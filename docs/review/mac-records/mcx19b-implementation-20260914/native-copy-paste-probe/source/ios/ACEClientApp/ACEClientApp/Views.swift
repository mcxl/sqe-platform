import Foundation
import SwiftUI
import UIKit

struct RootView: View {
    @ObservedObject var state: SessionState

    var body: some View {
        #if DEBUG
        if let scenario = UITestScenario.current {
            ScenarioRootView(scenario: scenario).padding()
        }
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
                CurrentReleaseMessageView(message: message, retry: .refresh, retryAction: state.refresh, signOutAction: state.signOut)
            case .failure(let message, let retry):
                CurrentReleaseMessageView(message: message, retry: retry, retryAction: { state.retry(retry) }, signOutAction: retry == .refresh ? { state.signOut() } : nil)
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
            Text("Sign In")
                .font(.title2)
                .bold()
                .foregroundStyle(.primary)
                .accessibilityAddTraits(.isHeader)
                .accessibilityIdentifier("Sign In heading")
            Section {
                TextField("Username", text: $username, prompt: Text("Username").foregroundColor(Color(uiColor: .label)))
                    .textInputAutocapitalization(.never)
                    .accessibilityLabel("Username")
                SecureField("Password", text: $password, prompt: Text("Password").foregroundColor(Color(uiColor: .label)))
                    .textInputAutocapitalization(.never)
                    .accessibilityLabel("Password")
                if let message { Text(message) }
                Button {
                    let enteredUsername = username
                    let enteredPassword = password
                    username = ""
                    password = ""
                    submit(enteredUsername, enteredPassword)
                } label: {
                    Text("Sign in")
                        .frame(minWidth: 44, minHeight: 44, alignment: .leading)
                        .contentShape(Rectangle())
                }
                .accessibilityLabel("Sign in")
            }
        }
    }
}

struct CurrentReleaseMessageView: View {
    let message: String
    let retry: RetryAction
    let retryAction: () -> Void
    let signOutAction: (() -> Void)?

    var body: some View {
        VStack(spacing: 20) {
            HandlingLabel()
            Text(message).multilineTextAlignment(.center)
            Button { retryAction() } label: {
                Text(retry == .keychainRead ? "Try again" : "Refresh")
                    .frame(minWidth: 44, minHeight: 44, alignment: .leading)
                    .contentShape(Rectangle())
            }
            .accessibilityLabel(retry == .keychainRead ? "Retry saved sign-in read" : "Refresh current release")
            if let signOutAction {
                Button { signOutAction() } label: {
                    Text("Sign out")
                        .frame(minWidth: 44, minHeight: 44, alignment: .leading)
                        .contentShape(Rectangle())
                }
                .accessibilityLabel("Sign out")
            }
        }
    }
}

struct SafeMessageView: View {
    let message: String
    let action: (String, () -> Void)?
    var body: some View {
        VStack(spacing: 20) {
            Text(message).multilineTextAlignment(.center)
            if let action {
                Button { action.1() } label: {
                    Text(action.0)
                        .frame(minWidth: 44, minHeight: 44, alignment: .leading)
                        .contentShape(Rectangle())
                }
                .accessibilityLabel(action.0)
            }
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
            VStack(alignment: .leading, spacing: 20) {
                SectionHeader("Current Release")
                HandlingLabel()
                ReleaseCard {
                    Text("Release Details")
                        .font(.headline)
                        .accessibilityAddTraits(.isHeader)
                    ValueRow(field: .engagementName, value: release.engagementName)
                    ValueRow(field: .reviewStatus, value: release.reviewStatus)
                    ValueRow(field: .releaseVersion, value: String(release.releaseVersion))
                    ValueRow(field: .publishedAt, value: release.publishedAt)
                }
                if let conclusion = release.conclusion {
                    ReleaseCard {
                        SectionHeader("Conclusion")
                        ValueRow(field: .conclusionTitle, value: conclusion.title)
                        ValueRow(field: .conclusionSummary, value: conclusion.summary)
                        ValueRow(field: .evidenceReference, value: conclusion.evidenceReferenceID)
                    }
                }
                if !release.actions.isEmpty {
                    SectionHeader("Actions")
                    ForEach(Array(release.actions.enumerated()), id: \.offset) { index, action in
                        ReleaseCard {
                            Text("Action \(index + 1)")
                                .font(.headline)
                                .accessibilityAddTraits(.isHeader)
                            ValueRow(field: .actionDescription, value: action.description)
                            ValueRow(field: .actionOwner, value: action.owner)
                            ValueRow(field: .actionTargetDate, value: action.targetDate)
                            ValueRow(field: .actionStatus, value: action.status)
                        }
                        .accessibilityElement(children: .contain)
                    }
                }
                ForEach(notices, id: \.self) { notice in Text(notice) }
                Button { refresh() } label: {
                    Text("Refresh")
                        .frame(minWidth: 44, minHeight: 44, alignment: .leading)
                        .contentShape(Rectangle())
                }
                .accessibilityLabel("Refresh current release")
                Button { signOut() } label: {
                    Text("Sign out")
                        .frame(minWidth: 44, minHeight: 44, alignment: .leading)
                        .contentShape(Rectangle())
                }
                .accessibilityLabel("Sign out")
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }
}

private struct ReleaseCard<Content: View>: View {
    let content: Content

    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            content
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(Color(uiColor: .secondarySystemBackground), in: RoundedRectangle(cornerRadius: 12))
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
    @Environment(\.dynamicTypeSize) private var dynamicTypeSize

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            if dynamicTypeSize.isAccessibilitySize {
                fieldContents
                copyButton
            } else {
                HStack(alignment: .top, spacing: 12) {
                    fieldContents
                    copyButton
                }
            }
            if let confirmation {
                Text(confirmation)
                    .font(.body)
                    .foregroundStyle(.primary)
            }
        }
    }

    private var fieldContents: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(field.label)
                .font(.subheadline)
                .foregroundStyle(.primary)
            Text(value)
                .font(.body)
                .frame(maxWidth: .infinity, alignment: .leading)
                .fixedSize(horizontal: false, vertical: true)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(field.label): \(value)")
    }

    private var copyButton: some View {
        Button(action: copyValue) {
            Label("Copy", systemImage: "doc.on.doc")
                .frame(minWidth: 44, minHeight: 44)
                .contentShape(Rectangle())
        }
        .buttonStyle(.bordered)
        .tint(.primary)
        .accessibilityLabel("Copy \(field.label)")
    }

    private func copyValue() {
        ClipboardWriteContract.write(visibleValue: value, writtenAt: Date())
        let announcement = "Copied \(field.label)."
        confirmation = announcement
        UIAccessibility.post(notification: .announcement, argument: announcement as NSString)
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
