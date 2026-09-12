import SwiftUI
import UIKit

struct ACEReleaseSplitView: View {
    @State private var columnVisibility: NavigationSplitViewVisibility = .all
    @State private var preferredCompactColumn: NavigationSplitViewColumn = .detail
    @State private var selection: String? = "current-release"

    var body: some View {
        NavigationSplitView(
            columnVisibility: $columnVisibility,
            preferredCompactColumn: $preferredCompactColumn
        ) {
            List(selection: $selection) {
                Section {
                    NavigationLink("Current Release", value: "current-release")
                }
            }
            .navigationTitle("Releases")
        } detail: {
            NavigationStack {
                if selection == "current-release" {
                    ReleaseDetailView()
                } else {
                    ContentUnavailableView("No Release Selected", systemImage: "doc")
                }
            }
        }
    }
}

struct ReleaseDetailView: View {
    var body: some View {
        List {
            Section {
                ForEach(ReleaseDetailData.releaseFields, id: \.label) { field in
                    ReleaseCopyField(field: field, value: ReleaseDetailData.value(for: field))
                }
            } header: {
                Text("Release").foregroundStyle(Color.primary)
            }
            Section {
                ForEach(ReleaseDetailData.conclusionFields, id: \.label) { field in
                    ReleaseCopyField(field: field, value: ReleaseDetailData.value(for: field))
                }
            } header: {
                Text("Conclusion").foregroundStyle(Color.primary)
            }
            Section {
                ForEach(ReleaseDetailData.actionFields, id: \.label) { field in
                    ReleaseCopyField(field: field, value: ReleaseDetailData.value(for: field))
                }
            } header: {
                Text("Action").foregroundStyle(Color.primary)
            }
        }
        .navigationTitle("Release Details")
    }
}

private struct ReleaseCopyField: View {
    let field: CopyableReleaseField
    let value: String
    @State private var confirmation: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            VStack(alignment: .leading, spacing: 4) {
                Text(field.label).font(.headline).fixedSize(horizontal: false, vertical: true)
                Text(value)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .accessibilityElement(children: .combine)
            .accessibilityLabel("\(field.label): \(value)")
            Button {
                ClipboardWriteContract.write(visibleValue: value, writtenAt: Date())
                let announcement = "Copied \(field.label)."
                confirmation = announcement
                UIAccessibility.post(notification: .announcement, argument: announcement as NSString)
            } label: {
                Text("Copy \(field.label)")
                    .frame(minWidth: 44, minHeight: 44, alignment: .leading)
                    .contentShape(Rectangle())
            }
            .accessibilityLabel("Copy \(field.label)")
            if let confirmation {
                Text(confirmation)
            }
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
