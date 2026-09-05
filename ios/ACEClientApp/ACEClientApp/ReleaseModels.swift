import Foundation

struct ClientReleaseResponse: Codable, Sendable, Equatable {
    let engagementName: String
    let reviewStatus: String
    let releaseVersion: Int
    let publishedAt: String
    let conclusion: ClientConclusion?
    let actions: [ClientAction]

    enum CodingKeys: String, CodingKey {
        case engagementName = "engagement_name", reviewStatus = "review_status"
        case releaseVersion = "release_version", publishedAt = "published_at", conclusion, actions
    }

    func validated() throws -> ValidatedRelease {
        if (engagementName == "Release unavailable" || engagementName == "Engagement not found"),
           reviewStatus.isEmpty, releaseVersion == 0, publishedAt.isEmpty, conclusion == nil, actions.isEmpty {
            return .empty
        }
        guard releaseVersion > 0, !engagementName.isEmpty, !reviewStatus.isEmpty,
              Self.isCanonicalUTC(publishedAt) else { throw ReleaseValidationError.invalid }
        if let conclusion {
            guard !conclusion.title.isEmpty, !conclusion.summary.isEmpty,
                  !conclusion.evidenceReferenceID.isEmpty else { throw ReleaseValidationError.invalid }
        }
        for action in actions {
            guard !action.description.isEmpty, !action.owner.isEmpty,
                  Self.isCalendarDate(action.targetDate), action.status == "OPEN" || action.status == "COMPLETE" else {
                throw ReleaseValidationError.invalid
            }
        }
        return .release(self)
    }

    private static func isCanonicalUTC(_ value: String) -> Bool {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(secondsFromGMT: 0)
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.isLenient = false
        formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss'Z'"
        return formatter.date(from: value).map { formatter.string(from: $0) == value } ?? false
    }

    private static func isCalendarDate(_ value: String) -> Bool {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(secondsFromGMT: 0)
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.isLenient = false
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.date(from: value).map { formatter.string(from: $0) == value } ?? false
    }
}

struct ClientConclusion: Codable, Sendable, Equatable {
    let title: String
    let summary: String
    let evidenceReferenceID: String
    enum CodingKeys: String, CodingKey { case title, summary; case evidenceReferenceID = "evidence_reference_id" }
}

struct ClientAction: Codable, Sendable, Equatable {
    let description: String
    let owner: String
    let targetDate: String
    let status: String
    enum CodingKeys: String, CodingKey { case description, owner; case targetDate = "target_date"; case status }
}

enum ValidatedRelease: Sendable, Equatable { case empty, release(ClientReleaseResponse) }
enum ReleaseValidationError: Error { case invalid }
