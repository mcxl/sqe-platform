"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export default function ErrorPage() {
  return (
    <main className="mx-auto max-w-3xl p-6 sm:p-10">
      <Alert>
        <AlertTitle>Relationship Review Unavailable</AlertTitle>
        <AlertDescription>
          The pilot could not load the requested read-only relationship data. Try again later.
        </AlertDescription>
      </Alert>
    </main>
  );
}
