import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  engagements: defineTable({
    fixtureKey: v.string(),
    isFictional: v.boolean(),
    name: v.string(),
  }).index("by_fixtureKey", ["fixtureKey"]),

  relationshipReviews: defineTable({
    fixtureKey: v.string(),
    isFictional: v.boolean(),
    engagementId: v.id("engagements"),
    title: v.string(),
    relationshipType: v.string(),
    materialRisk: v.string(),
    materialRiskOrder: v.number(),
    waitingSince: v.string(),
    rationale: v.string(),
    sourceSupport: v.array(v.string()),
    gaps: v.array(v.string()),
    contradictions: v.array(v.string()),
    currentVersionId: v.optional(v.id("relationshipVersions")),
  })
    .index("by_fixtureKey", ["fixtureKey"])
    .index("by_isFictional_and_materialRiskOrder_and_waitingSince", [
      "isFictional",
      "materialRiskOrder",
      "waitingSince",
    ]),

  relationshipVersions: defineTable({
    fixtureKey: v.string(),
    isFictional: v.boolean(),
    reviewId: v.id("relationshipReviews"),
    versionNumber: v.number(),
    label: v.string(),
    recordedOn: v.string(),
    summary: v.string(),
    sourceSupport: v.array(v.string()),
  })
    .index("by_fixtureKey", ["fixtureKey"])
    .index("by_reviewId_and_isFictional_and_versionNumber", [
      "reviewId",
      "isFictional",
      "versionNumber",
    ]),

  auditorDecisions: defineTable({
    fixtureKey: v.string(),
    isFictional: v.boolean(),
    reviewId: v.id("relationshipReviews"),
    versionId: v.id("relationshipVersions"),
    decision: v.string(),
    recordedOn: v.string(),
    basis: v.string(),
  })
    .index("by_fixtureKey", ["fixtureKey"])
    .index("by_reviewId_and_isFictional_and_recordedOn", [
      "reviewId",
      "isFictional",
      "recordedOn",
    ]),
});
