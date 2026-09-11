import Foundation

enum ReleaseDetailData {
    static let release = ClientReleaseResponse(
        engagementName: "Fictional Engagement",
        reviewStatus: "RELEASED",
        releaseVersion: 1,
        publishedAt: "2026-08-24T10:15:30Z",
        conclusion: ClientConclusion(
            title: "Fictional conclusion",
            summary: "Fictional summary",
            evidenceReferenceID: "FICTIONAL-REF-001"
        ),
        actions: [
            ClientAction(
                description: "Fictional action",
                owner: "Fictional owner",
                targetDate: "2026-08-25",
                status: "OPEN"
            )
        ]
    )

    static let releaseFields: [CopyableReleaseField] = [.engagementName, .reviewStatus, .releaseVersion, .publishedAt]
    static let conclusionFields: [CopyableReleaseField] = [.conclusionTitle, .conclusionSummary, .evidenceReference]
    static let actionFields: [CopyableReleaseField] = [.actionDescription, .actionOwner, .actionTargetDate, .actionStatus]

    static func value(for field: CopyableReleaseField) -> String {
        switch field {
        case .engagementName: release.engagementName
        case .reviewStatus: release.reviewStatus
        case .releaseVersion: String(release.releaseVersion)
        case .publishedAt: release.publishedAt
        case .conclusionTitle: release.conclusion?.title ?? ""
        case .conclusionSummary: release.conclusion?.summary ?? ""
        case .evidenceReference: release.conclusion?.evidenceReferenceID ?? ""
        case .actionDescription: release.actions.first?.description ?? ""
        case .actionOwner: release.actions.first?.owner ?? ""
        case .actionTargetDate: release.actions.first?.targetDate ?? ""
        case .actionStatus: release.actions.first?.status ?? ""
        }
    }
}

enum CopyableReleaseField: CaseIterable {
    case engagementName, reviewStatus, releaseVersion, publishedAt, conclusionTitle, conclusionSummary, evidenceReference, actionDescription, actionOwner, actionTargetDate, actionStatus

    var label: String {
        switch self {
        case .engagementName: "Engagement name"
        case .reviewStatus: "Review status"
        case .releaseVersion: "Release version"
        case .publishedAt: "Published date and time"
        case .conclusionTitle: "Conclusion title"
        case .conclusionSummary: "Conclusion summary"
        case .evidenceReference: "Evidence reference"
        case .actionDescription: "Action description"
        case .actionOwner: "Action owner"
        case .actionTargetDate: "Action target date"
        case .actionStatus: "Action status"
        }
    }
}
