import type { GenericMutationCtx } from "convex/server";
import { v } from "convex/values";
import type { DataModel } from "./_generated/dataModel";
import { internalMutation } from "./_generated/server.js";

type SeedReview = {
  fixtureKey: string;
  engagementId: DataModel["relationshipReviews"]["document"]["engagementId"];
  title: string;
  relationshipType: string;
  materialRisk: string;
  materialRiskOrder: number;
  waitingSince: string;
  rationale: string;
  sourceSupport: string[];
  gaps: string[];
  contradictions: string[];
};

const insertReviewHistory = async (
  ctx: GenericMutationCtx<DataModel>,
  review: SeedReview,
  versions: Array<{
    fixtureKey: string;
    versionNumber: number;
    label: string;
    recordedOn: string;
    summary: string;
    sourceSupport: string[];
  }>,
  decision: { fixtureKey: string; decision: string; recordedOn: string; basis: string },
) => {
  const reviewId = await ctx.db.insert("relationshipReviews", {
    ...review,
    isFictional: true,
  });
  const versionIds = [];

  for (const version of versions) {
    versionIds.push(
      await ctx.db.insert("relationshipVersions", {
        ...version,
        isFictional: true,
        reviewId,
      }),
    );
  }

  const currentVersionId = versionIds[versionIds.length - 1];
  if (currentVersionId === undefined) {
    throw new Error("A fictional review needs a current version.");
  }

  await ctx.db.patch(reviewId, { currentVersionId });
  await ctx.db.insert("auditorDecisions", {
    ...decision,
    isFictional: true,
    reviewId,
    versionId: currentVersionId,
  });
};

export const seedPilotData = internalMutation({
  args: {},
  returns: v.object({ inserted: v.number() }),
  handler: async (ctx) => {
    const existing = await ctx.db
      .query("engagements")
      .withIndex("by_fixtureKey", (q) => q.eq("fixtureKey", "fictional-orchid"))
      .first();

    if (existing !== null) {
      return { inserted: 0 };
    }

    const orchidEngagementId = await ctx.db.insert("engagements", {
      fixtureKey: "fictional-orchid",
      isFictional: true,
      name: "Orchid Works Fictional Engagement",
    });
    const juniperEngagementId = await ctx.db.insert("engagements", {
      fixtureKey: "fictional-juniper",
      isFictional: true,
      name: "Juniper Field Fictional Engagement",
    });
    const cedarEngagementId = await ctx.db.insert("engagements", {
      fixtureKey: "fictional-cedar",
      isFictional: true,
      name: "Cedar Advisory Fictional Engagement",
    });

    await insertReviewHistory(
      ctx,
      {
        fixtureKey: "fictional-orchid-harbour",
        engagementId: orchidEngagementId,
        title: "Orchid Works And Harbour Records",
        relationshipType: "Service delivery dependency",
        materialRisk: "High",
        materialRiskOrder: 1,
        waitingSince: "2026-06-01",
        rationale: "The fictional service register identifies Harbour Records as a retained archive provider.",
        sourceSupport: ["Fictional service register, version 2.0"],
        gaps: ["No fictional exit plan is recorded."],
        contradictions: ["Fictional procurement and service records use different dependency terms."],
      },
      [
        {
          fixtureKey: "fictional-orchid-harbour-v1",
          versionNumber: 1,
          label: "Version 1.0",
          recordedOn: "2026-06-01",
          summary: "Initial fictional relationship assessment.",
          sourceSupport: ["Fictional service register, version 1.0"],
        },
        {
          fixtureKey: "fictional-orchid-harbour-v2",
          versionNumber: 2,
          label: "Version 2.0",
          recordedOn: "2026-07-01",
          summary: "Current fictional relationship assessment.",
          sourceSupport: ["Fictional service register, version 2.0"],
        },
      ],
      {
        fixtureKey: "fictional-orchid-harbour-decision",
        decision: "Retain for relationship review",
        recordedOn: "2026-07-02",
        basis: "Fictional source records contain different dependency statements.",
      },
    );

    await insertReviewHistory(
      ctx,
      {
        fixtureKey: "fictional-juniper-archive",
        engagementId: juniperEngagementId,
        title: "Juniper Field And Archive Service",
        relationshipType: "Information retention dependency",
        materialRisk: "High",
        materialRiskOrder: 1,
        waitingSince: "2026-06-15",
        rationale: "The fictional records describe a retained archive service.",
        sourceSupport: ["Fictional archive register"],
        gaps: [],
        contradictions: [],
      },
      [
        {
          fixtureKey: "fictional-juniper-archive-v1",
          versionNumber: 1,
          label: "Version 1.0",
          recordedOn: "2026-06-15",
          summary: "Current fictional archive dependency assessment.",
          sourceSupport: ["Fictional archive register"],
        },
      ],
      {
        fixtureKey: "fictional-juniper-archive-decision",
        decision: "Keep in review queue",
        recordedOn: "2026-06-16",
        basis: "The fictional archive dependency needs review.",
      },
    );

    await insertReviewHistory(
      ctx,
      {
        fixtureKey: "fictional-cedar-support",
        engagementId: cedarEngagementId,
        title: "Cedar Advisory And Support Desk",
        relationshipType: "Operational support dependency",
        materialRisk: "Medium",
        materialRiskOrder: 2,
        waitingSince: "2026-05-15",
        rationale: "The fictional support agreement identifies an operational support dependency.",
        sourceSupport: ["Fictional support agreement"],
        gaps: ["No fictional service measurement is recorded."],
        contradictions: [],
      },
      [
        {
          fixtureKey: "fictional-cedar-support-v1",
          versionNumber: 1,
          label: "Version 1.0",
          recordedOn: "2026-05-15",
          summary: "Current fictional support dependency assessment.",
          sourceSupport: ["Fictional support agreement"],
        },
      ],
      {
        fixtureKey: "fictional-cedar-support-decision",
        decision: "Monitor in review queue",
        recordedOn: "2026-05-16",
        basis: "The fictional support agreement is incomplete.",
      },
    );

    return { inserted: 3 };
  },
});
