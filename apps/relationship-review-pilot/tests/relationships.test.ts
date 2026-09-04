import { convexTest } from "convex-test";
import { describe, expect, it } from "vitest";
import { api, internal } from "../convex/_generated/api";
import schema from "../convex/schema";

const modules = import.meta.glob([
  "../convex/**/*.ts",
  "../convex/**/*.js",
  "!../convex/**/*.d.ts",
]);

function createTest() {
  return convexTest({ schema, modules });
}

describe("relationship review queries", () => {
  it("returns an empty public queue before fictional seed data exists", async () => {
    const t = createTest();

    await expect(t.query(api.relationships.listQueue, {})).resolves.toEqual([]);
  });

  it("orders fictional reviews by material risk and then oldest waiting proposal", async () => {
    const t = createTest();
    await t.mutation(internal.seed.seedPilotData, {});

    const queue = await t.query(api.relationships.listQueue, {});

    expect(queue.map((item) => item.title)).toEqual([
      "Orchid Works And Harbour Records",
      "Juniper Field And Archive Service",
      "Cedar Advisory And Support Desk",
    ]);
    expect(queue.map((item) => item.materialRisk)).toEqual(["High", "High", "Medium"]);
    expect(queue.map((item) => item.waitingSince)).toEqual([
      "2026-06-01",
      "2026-06-15",
      "2026-05-15",
    ]);
  });

  it("returns current and linked immutable history records", async () => {
    const t = createTest();
    await t.mutation(internal.seed.seedPilotData, {});
    const queue = await t.query(api.relationships.listQueue, {});
    const detail = await t.query(api.relationships.getRelationship, { id: queue[0]!._id });

    expect(detail.state).toBe("ready");
    if (detail.state === "ready") {
      expect(detail.record.engagement.name).toBe("Orchid Works Fictional Engagement");
      expect(detail.record.currentVersion.label).toBe("Version 2.0");
      expect(detail.record.earlierVersions.map((version) => version.label)).toEqual(["Version 1.0"]);
      expect(detail.record.earlierDecisions).toHaveLength(1);
      expect(detail.record.earlierDecisions[0]?.versionId).toBe(detail.record.currentVersion._id);
    }
  });

  it("returns missing and blocked public results without record fields", async () => {
    const t = createTest();
    await t.mutation(internal.seed.seedPilotData, {});
    const engagementId = await t.run(async (ctx) => {
      const engagement = await ctx.db
        .query("engagements")
        .withIndex("by_fixtureKey", (q) => q.eq("fixtureKey", "fictional-orchid"))
        .unique();
      if (engagement === null) throw new Error("Expected fictional engagement.");
      return engagement._id;
    });

    const [missingId, blockedId] = await t.run(async (ctx) => {
      const missing = await ctx.db.insert("relationshipReviews", {
        fixtureKey: "test-missing-review",
        isFictional: true,
        engagementId,
        title: "Missing test review",
        relationshipType: "Test",
        materialRisk: "Low",
        materialRiskOrder: 3,
        waitingSince: "2026-08-01",
        rationale: "Test control.",
        sourceSupport: [],
        gaps: [],
        contradictions: [],
      });
      const blocked = await ctx.db.insert("relationshipReviews", {
        fixtureKey: "test-blocked-review",
        isFictional: false,
        engagementId,
        title: "Blocked test control",
        relationshipType: "Test",
        materialRisk: "Low",
        materialRiskOrder: 3,
        waitingSince: "2026-08-02",
        rationale: "Test control.",
        sourceSupport: [],
        gaps: [],
        contradictions: [],
      });
      return [missing, blocked];
    });

    await expect(t.query(api.relationships.getRelationship, { id: missingId })).resolves.toEqual({ state: "missing" });
    await expect(t.query(api.relationships.getRelationship, { id: blockedId })).resolves.toEqual({ state: "blocked" });
  });

  it("does not change existing versions or decisions on a second seed", async () => {
    const t = createTest();
    await t.mutation(internal.seed.seedPilotData, {});
    const queue = await t.query(api.relationships.listQueue, {});
    const before = await t.query(api.relationships.getRelationship, { id: queue[0]!._id });
    if (before.state !== "ready") throw new Error("Expected ready fictional review.");

    await expect(t.mutation(internal.seed.seedPilotData, {})).resolves.toEqual({ inserted: 0 });
    const after = await t.query(api.relationships.getRelationship, { id: queue[0]!._id });

    expect(after).toEqual(before);
  });
});
