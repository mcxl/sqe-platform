import { ConvexClientProvider } from "@/components/convex-client-provider";
import { RelationshipReviewWorkbench } from "@/components/relationship-review-workbench";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export default function HomePage() {
  const convexUrl = process.env.NEXT_PUBLIC_CONVEX_URL;

  return (
    <main className="mx-auto max-w-7xl p-6 sm:p-10">
      <header className="mb-8">
        <p className="text-sm font-medium text-slate-600">Read-Only Fictional Pilot</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-950">
          Relationship Review
        </h1>
      </header>
      {convexUrl === undefined || convexUrl.length === 0 ? (
        <Alert>
          <AlertTitle>Pilot Connection Not Configured</AlertTitle>
          <AlertDescription>
            Set NEXT_PUBLIC_CONVEX_URL to connect this read-only fictional pilot.
          </AlertDescription>
        </Alert>
      ) : (
        <ConvexClientProvider url={convexUrl}>
          <RelationshipReviewWorkbench />
        </ConvexClientProvider>
      )}
    </main>
  );
}
