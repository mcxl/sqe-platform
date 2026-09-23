import { v } from "convex/values";
import { query } from "./_generated/server.js";

const engagementValidator = v.object({
  _id: v.id("engagements"),
  name: v.string(),
});

const relationshipVersionValidator = v.object({
  _id: v.id("relationshipVersions"),
  reviewId: v.id("relationshipReviews"),
  versionNumber: v.number(),
  label: v.string(),
  recordedOn: v.string(),
  summary: v.string(),
  sourceSupport: v.array(v.string()),
});

const auditorDecisionValidator = v.object({
  _id: v.id("auditorDecisions"),
  reviewId: v.id("relationshipReviews"),
  versionId: v.id("relationshipVersions"),
  decision: v.string(),
  recordedOn: v.string(),
  basis: v.string(),
});

const queueItemValidator = v.object({
  _id: v.id("relationshipReviews"),
  title: v.string(),
  relationshipType: v.string(),
  materialRisk: v.string(),
  waitingSince: v.string(),
});

const readyRecordValidator = v.object({
  _id: v.id("relationshipReviews"),
  title: v.string(),
  relationshipType: v.string(),
  materialRisk: v.string(),
  waitingSince: v.string(),
  rationale: v.string(),
  sourceSupport: v.array(v.string()),
  gaps: v.array(v.string()),
  contradictions: v.array(v.string()),
  engagement: engagementValidator,
  currentVersion: relationshipVersionValidator,
  earlierVersions: v.array(relationshipVersionValidator),
  earlierDecisions: v.array(auditorDecisionValidator),
});

export const listQueue = query({
  args: {},
  returns: v.array(queueItemValidator),
  handler: async (ctx) => {
    const reviews = await ctx.db
      .query("relationshipReviews")
      .withIndex("by_isFictional_and_materialRiskOrder_and_waitingSince", (q) =>
        q.eq("isFictional", true),
      )
      .take(25);

    return reviews.map((review) => ({
      _id: review._id,
      title: review.title,
      relationshipType: review.relationshipType,
      materialRisk: review.materialRisk,
      waitingSince: review.waitingSince,
    }));
  },
});

export const getRelationship = query({
  args: { id: v.id("relationshipReviews") },
  returns: v.union(
    v.object({ state: v.literal("missing") }),
    v.object({ state: v.literal("blocked") }),
    v.object({ state: v.literal("ready"), record: readyRecordValidator }),
  ),
  handler: async (ctx, args) => {
    const review = await ctx.db
      .query("relationshipReviews")
      .withIndex("by_id", (q) => q.eq("_id", args.id))
      .unique();

    if (review === null) {
      return { state: "missing" as const };
    }

    if (!review.isFictional) {
      return { state: "blocked" as const };
    }

    if (review.currentVersionId === undefined) {
      return { state: "missing" as const };
    }
    const currentVersionId = review.currentVersionId;

    const engagement = await ctx.db
      .query("engagements")
      .withIndex("by_id", (q) => q.eq("_id", review.engagementId))
      .unique();
    const currentVersion = await ctx.db
      .query("relationshipVersions")
      .withIndex("by_id", (q) => q.eq("_id", currentVersionId))
      .unique();

    if (
      engagement === null ||
      !engagement.isFictional ||
      currentVersion === null ||
      !currentVersion.isFictional
    ) {
      return { state: "blocked" as const };
    }

    const earlierVersions = await ctx.db
      .query("relationshipVersions")
      .withIndex("by_reviewId_and_isFictional_and_versionNumber", (q) =>
        q
          .eq("reviewId", review._id)
          .eq("isFictional", true)
          .lt("versionNumber", currentVersion.versionNumber),
      )
      .take(25);
    const earlierDecisions = await ctx.db
      .query("auditorDecisions")
      .withIndex("by_reviewId_and_isFictional_and_recordedOn", (q) =>
        q.eq("reviewId", review._id).eq("isFictional", true),
      )
      .take(25);

    return {
      state: "ready" as const,
      record: {
        _id: review._id,
        title: review.title,
        relationshipType: review.relationshipType,
        materialRisk: review.materialRisk,
        waitingSince: review.waitingSince,
        rationale: review.rationale,
        sourceSupport: review.sourceSupport,
        gaps: review.gaps,
        contradictions: review.contradictions,
        engagement: { _id: engagement._id, name: engagement.name },
        currentVersion: {
          _id: currentVersion._id,
          reviewId: currentVersion.reviewId,
          versionNumber: currentVersion.versionNumber,
          label: currentVersion.label,
          recordedOn: currentVersion.recordedOn,
          summary: currentVersion.summary,
          sourceSupport: currentVersion.sourceSupport,
        },
        earlierVersions: earlierVersions.map((version) => ({
          _id: version._id,
          reviewId: version.reviewId,
          versionNumber: version.versionNumber,
          label: version.label,
          recordedOn: version.recordedOn,
          summary: version.summary,
          sourceSupport: version.sourceSupport,
        })),
        earlierDecisions: earlierDecisions.map((decision) => ({
          _id: decision._id,
          reviewId: decision.reviewId,
          versionId: decision.versionId,
          decision: decision.decision,
          recordedOn: decision.recordedOn,
          basis: decision.basis,
        })),
      },
    };
  },
});
