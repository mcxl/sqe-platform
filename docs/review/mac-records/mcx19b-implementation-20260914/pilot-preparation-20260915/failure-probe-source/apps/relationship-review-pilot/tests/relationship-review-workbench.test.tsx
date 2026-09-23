import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { Id } from "../convex/_generated/dataModel";

const { useQuery } = vi.hoisted(() => ({ useQuery: vi.fn() }));

vi.mock("convex/react", () => ({ useQuery }));

import ErrorPage from "../app/error";
import { RelationshipReviewWorkbench } from "../components/relationship-review-workbench";

const reviewId = "j57f4c0a1b2c3d4e5f6g7h8i" as Id<"relationshipReviews">;
const secondReviewId = "j57f4c0a1b2c3d4e5f6g7h8j" as Id<"relationshipReviews">;
const versionId = "j57f4c0a1b2c3d4e5f6g7h8k" as Id<"relationshipVersions">;
const earlierVersionId = "j57f4c0a1b2c3d4e5f6g7h8l" as Id<"relationshipVersions">;
const engagementId = "j57f4c0a1b2c3d4e5f6g7h8m" as Id<"engagements">;
const decisionId = "j57f4c0a1b2c3d4e5f6g7h8n" as Id<"auditorDecisions">;

const queue = [
  {
    _id: reviewId,
    title: "Orchid Works And Harbour Records",
    relationshipType: "Service delivery dependency",
    materialRisk: "High",
    waitingSince: "2026-06-01",
  },
  {
    _id: secondReviewId,
    title: "Juniper Field And Archive Service",
    relationshipType: "Information retention dependency",
    materialRisk: "High",
    waitingSince: "2026-06-15",
  },
];

const readyDetail = {
  state: "ready",
  record: {
    _id: reviewId,
    title: "Orchid Works And Harbour Records",
    relationshipType: "Service delivery dependency",
    materialRisk: "High",
    waitingSince: "2026-06-01",
    rationale: "The fictional register identifies a service dependency.",
    sourceSupport: ["Fictional service register"],
    gaps: ["No fictional exit plan is recorded."],
    contradictions: ["Fictional documents use different dependency terms."],
    engagement: { _id: engagementId, name: "Orchid Works Fictional Engagement" },
    currentVersion: {
      _id: versionId,
      reviewId,
      versionNumber: 2,
      label: "Version 2.0",
      recordedOn: "2026-07-01",
      summary: "Current fictional relationship assessment.",
      sourceSupport: ["Fictional service register"],
    },
    earlierVersions: [
      {
        _id: earlierVersionId,
        reviewId,
        versionNumber: 1,
        label: "Version 1.0",
        recordedOn: "2026-06-01",
        summary: "Initial fictional relationship assessment.",
        sourceSupport: ["Fictional service register"],
      },
    ],
    earlierDecisions: [
      {
        _id: decisionId,
        reviewId,
        versionId,
        decision: "Retain for relationship review",
        recordedOn: "2026-07-02",
        basis: "Fictional records differ.",
      },
    ],
  },
};

function configureQueries(queueResult: unknown, detailResult: unknown = undefined) {
  useQuery.mockImplementation((_reference: unknown, args: unknown) => {
    if (args === "skip") return undefined;
    if (typeof args === "object" && args !== null && "id" in args) return detailResult;
    return queueResult;
  });
}

beforeEach(() => useQuery.mockReset());
afterEach(() => {
  cleanup();
  window.history.replaceState({}, "", "/");
});

it("shows loading and empty states", () => {
  configureQueries(undefined);
  const { rerender } = render(<RelationshipReviewWorkbench />);
  expect(screen.getByLabelText("Loading relationship review queue")).toBeInTheDocument();

  configureQueries([]);
  rerender(<RelationshipReviewWorkbench />);
  expect(screen.getByText("No Relationships To Review")).toBeInTheDocument();
});

it("uses queue links with href values, type and selected-item interaction", () => {
  configureQueries(queue, readyDetail);
  render(<RelationshipReviewWorkbench />);

  const orchid = screen.getByRole("link", { name: "Orchid Works And Harbour Records" });
  expect(orchid).toHaveAttribute("href", `/?relationship=${reviewId}`);
  expect(screen.getByRole("link", { name: "Juniper Field And Archive Service" })).toHaveAttribute(
    "href",
    `/?relationship=${secondReviewId}`,
  );
  expect(screen.getByText("Type")).toBeInTheDocument();
  expect(screen.getByText("Service delivery dependency")).toBeInTheDocument();

  fireEvent.click(orchid);
  expect(window.location.search).toBe(`?relationship=${reviewId}`);
  expect(screen.getByText("Current Version")).toBeInTheDocument();
  expect(screen.getByText("Version 2.0 — 2026-07-01")).toBeInTheDocument();
  expect(screen.getByText("Earlier Versions")).toBeInTheDocument();
  expect(screen.getByText("Version 1.0 — 2026-06-01")).toBeInTheDocument();
  expect(screen.getByText("Owner")).toBeInTheDocument();
  expect(screen.getByText("Orchid Works Fictional Engagement")).toBeInTheDocument();
  expect(screen.getByText("Status")).toBeInTheDocument();
  expect(screen.getByText("Waiting For Review")).toBeInTheDocument();
  expect(screen.getByText("Evidence")).toBeInTheDocument();
  expect(screen.getByText("Fictional service register")).toBeInTheDocument();
  expect(screen.getByText("Gaps")).toBeInTheDocument();
  expect(screen.getByText("No fictional exit plan is recorded.")).toBeInTheDocument();
  expect(screen.getByText("Review Notes")).toBeInTheDocument();
  expect(screen.getByText("Retain for relationship review")).toBeInTheDocument();
  expect(screen.getByText("Fictional records differ.")).toBeInTheDocument();
  expect(screen.getByText("2026-07-02")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /approve|edit|delete|upload/i })).not.toBeInTheDocument();
  expect(screen.queryByRole("link", { name: /approve|edit|delete|upload|decision/i })).not.toBeInTheDocument();
});

it("restores the selected item from a direct relationship query URL", async () => {
  window.history.replaceState({}, "", `/?relationship=${reviewId}`);
  configureQueries(queue, readyDetail);

  render(<RelationshipReviewWorkbench />);

  expect(await screen.findByText("Current Version")).toBeInTheDocument();
  expect(screen.getByText("Version 2.0 — 2026-07-01")).toBeInTheDocument();
});

it("shows that no review notes are recorded", () => {
  configureQueries(queue, {
    ...readyDetail,
    record: { ...readyDetail.record, earlierDecisions: [] },
  });
  render(<RelationshipReviewWorkbench />);

  fireEvent.click(screen.getByRole("link", { name: "Orchid Works And Harbour Records" }));
  expect(screen.getByText("Review Notes")).toBeInTheDocument();
  expect(screen.getByText("None recorded.")).toBeInTheDocument();
});

it("shows not found and skips the detail query for an incorrect relationship URL", async () => {
  window.history.replaceState({}, "", "/?relationship=incorrect-relationship-id");
  configureQueries(queue, readyDetail);

  render(<RelationshipReviewWorkbench />);

  expect(await screen.findByText("Relationship Not Found")).toBeInTheDocument();
  expect(useQuery.mock.calls.map(([, args]) => args)).toContain("skip");
  expect(useQuery.mock.calls.some(([, args]) => typeof args === "object" && args !== null && "id" in args)).toBe(false);
});

it("synchronises selection from browser history popstate", async () => {
  configureQueries(queue, readyDetail);
  render(<RelationshipReviewWorkbench />);

  fireEvent.click(screen.getByRole("link", { name: "Orchid Works And Harbour Records" }));
  expect(screen.getByText("Current Version")).toBeInTheDocument();

  window.history.pushState({}, "", "/");
  window.dispatchEvent(new PopStateEvent("popstate"));

  await waitFor(() => expect(screen.getByText("Select A Relationship")).toBeInTheDocument());
  await waitFor(() => expect(useQuery.mock.calls.at(-1)?.[1]).toBe("skip"));
});

it("shows missing and blocked states without record data", () => {
  configureQueries(queue, { state: "missing" });
  const { rerender } = render(<RelationshipReviewWorkbench />);
  fireEvent.click(screen.getByRole("link", { name: "Orchid Works And Harbour Records" }));
  expect(screen.getByText("Relationship Not Found")).toBeInTheDocument();

  configureQueries(queue, { state: "blocked" });
  rerender(<RelationshipReviewWorkbench />);
  expect(screen.getByText("Relationship Blocked")).toBeInTheDocument();
});

it("shows the route error state", () => {
  render(<ErrorPage />);
  expect(screen.getByText("Relationship Review Unavailable")).toBeInTheDocument();
});
