"use client";

import { useQuery } from "convex/react";
import type { FunctionReturnType } from "convex/server";
import { useEffect, useState } from "react";
import { api } from "@/convex/_generated/api";
import { Alert, AlertDescription, AlertTitle } from "./ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Skeleton } from "./ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";

type RelationshipResult = FunctionReturnType<typeof api.relationships.getRelationship>;

function ListSection({ title, entries }: { title: string; entries: string[] }) {
  return (
    <section>
      <h3 className="font-medium text-slate-900">{title}</h3>
      {entries.length === 0 ? (
        <p className="mt-1 text-sm text-slate-600">None recorded.</p>
      ) : (
        <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-slate-700">
          {entries.map((entry) => <li key={entry}>{entry}</li>)}
        </ul>
      )}
    </section>
  );
}

function QueueLoading() {
  return (
    <Card aria-label="Loading relationship review queue">
      <CardHeader><CardTitle>Relationship Review Queue</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <Skeleton className="h-6 w-2/3" />
        <Skeleton className="h-6 w-full" />
        <Skeleton className="h-6 w-5/6" />
      </CardContent>
    </Card>
  );
}

function selectedIdFromLocation(): string | undefined {
  if (typeof window === "undefined") return undefined;
  const selectedId = new URLSearchParams(window.location.search).get("relationship");
  return selectedId === null ? undefined : selectedId;
}

export function RelationshipReviewWorkbench() {
  const [selectedId, setSelectedId] = useState<string | undefined>(selectedIdFromLocation);
  useEffect(() => {
    const syncSelectedId = () => setSelectedId(selectedIdFromLocation());
    window.addEventListener("popstate", syncSelectedId);
    return () => window.removeEventListener("popstate", syncSelectedId);
  }, []);
  const queue = useQuery(api.relationships.listQueue, {});
  const selectedQueueItem = queue?.find((item) => item._id === selectedId);
  const detail = useQuery(
    api.relationships.getRelationship,
    selectedQueueItem === undefined ? "skip" : { id: selectedQueueItem._id },
  );

  if (queue === undefined) return <QueueLoading />;
  if (queue.length === 0 && selectedId === undefined) {
    return <Alert><AlertTitle>No Relationships To Review</AlertTitle><AlertDescription>The fictional relationship-review queue is empty.</AlertDescription></Alert>;
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
      <Card>
        <CardHeader><CardTitle>Relationship Review Queue</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader><TableRow><TableHead>Relationship</TableHead><TableHead>Type</TableHead><TableHead>Material Risk</TableHead><TableHead>Waiting Since</TableHead></TableRow></TableHeader>
            <TableBody>
              {queue.map((item) => (
                <TableRow key={item._id}>
                  <TableCell>
                    <a
                      href={`/?relationship=${item._id}`}
                      className="font-medium text-blue-800 underline-offset-4 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2"
                      onClick={(event) => {
                        event.preventDefault();
                        setSelectedId(item._id);
                        const url = new URL(window.location.href);
                        url.searchParams.set("relationship", item._id);
                        window.history.pushState({}, "", `${url.pathname}${url.search}${url.hash}`);
                      }}
                    >
                      {item.title}
                    </a>
                  </TableCell>
                  <TableCell>{item.relationshipType}</TableCell>
                  <TableCell>{item.materialRisk}</TableCell>
                  <TableCell>{item.waitingSince}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
      <RelationshipDetail
        detail={detail}
        selected={selectedId !== undefined}
        selectionMissing={selectedId !== undefined && selectedQueueItem === undefined}
      />
    </div>
  );
}

function RelationshipDetail({ detail, selected, selectionMissing }: { detail: RelationshipResult | undefined; selected: boolean; selectionMissing: boolean }) {
  if (!selected) {
    return <Alert><AlertTitle>Select A Relationship</AlertTitle><AlertDescription>Select a fictional queue item to view its read-only evidence.</AlertDescription></Alert>;
  }
  if (selectionMissing) {
    return <Alert><AlertTitle>Relationship Not Found</AlertTitle><AlertDescription>The selected relationship is not available in this pilot.</AlertDescription></Alert>;
  }
  if (detail === undefined) {
    return <Card aria-label="Loading relationship detail"><CardContent className="space-y-3 pt-5"><Skeleton className="h-7 w-3/4" /><Skeleton className="h-5 w-full" /><Skeleton className="h-5 w-5/6" /></CardContent></Card>;
  }
  if (detail.state === "missing") {
    return <Alert><AlertTitle>Relationship Not Found</AlertTitle><AlertDescription>The selected relationship is not available in this pilot.</AlertDescription></Alert>;
  }
  if (detail.state === "blocked") {
    return <Alert><AlertTitle>Relationship Blocked</AlertTitle><AlertDescription>This record is outside the fictional pilot data set.</AlertDescription></Alert>;
  }

  const { record } = detail;
  return (
    <Card>
      <CardHeader><CardTitle>{record.title}</CardTitle></CardHeader>
      <CardContent className="space-y-6 text-slate-700">
        <section><h3 className="font-medium text-slate-900">Relationship Type</h3><p className="mt-1 text-sm">{record.relationshipType}</p></section>
        <section><h3 className="font-medium text-slate-900">Material Risk</h3><p className="mt-1 text-sm">{record.materialRisk}</p></section>
        <section><h3 className="font-medium text-slate-900">Rationale</h3><p className="mt-1 text-sm">{record.rationale}</p></section>
        <section><h3 className="font-medium text-slate-900">Owner</h3><p className="mt-1 text-sm">{record.engagement.name}</p></section>
        <section><h3 className="font-medium text-slate-900">Status</h3><p className="mt-1 text-sm">Waiting For Review</p></section>
        <section><h3 className="font-medium text-slate-900">Current Version</h3><p className="mt-1 text-sm">{record.currentVersion.label} — {record.currentVersion.recordedOn}</p><p className="mt-1 text-sm">{record.currentVersion.summary}</p></section>
        <ListSection title="Evidence" entries={record.sourceSupport} />
        <ListSection title="Gaps" entries={record.gaps} />
        <ListSection title="Contradictions" entries={record.contradictions} />
        <section>
          <h3 className="font-medium text-slate-900">Earlier Versions</h3>
          {record.earlierVersions.length === 0 ? <p className="mt-1 text-sm text-slate-600">None recorded.</p> : <ul className="mt-1 space-y-2 text-sm">{record.earlierVersions.map((version) => <li key={version._id}><p>{version.label} — {version.recordedOn}</p><p className="text-slate-600">{version.summary}</p></li>)}</ul>}
        </section>
        <section>
          <h3 className="font-medium text-slate-900">Review Notes</h3>
          {record.earlierDecisions.length === 0 ? <p className="mt-1 text-sm text-slate-600">None recorded.</p> : <ul className="mt-1 space-y-2 text-sm">{record.earlierDecisions.map((decision) => <li key={decision._id}><p>{decision.decision}</p><p>{decision.basis}</p><p className="text-slate-600">{decision.recordedOn}</p></li>)}</ul>}
        </section>
      </CardContent>
    </Card>
  );
}
