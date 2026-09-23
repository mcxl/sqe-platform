# Convex And Vercel Fictional Relationship View Pilot

## Problem Statement

The SQE workbench is a local Python application with SQLite storage.

It does not provide a shared web interface or live data updates.

The user has approved a Convex and Vercel pilot.

The pilot must not expose real client information or change the current workbench.

## Solution

Build an isolated read-only Relationship View pilot.

Use Next.js for the web interface.

Use Convex for fictional Relationship Review data and read queries.

Use Vercel for preview deployment.

Keep the Python workbench unchanged.

## User Stories

1. As an auditor, I want a web Relationship Review queue, so that I can open fictional review items remotely.
2. As an auditor, I want relationship titles and types, so that I can select the correct item.
3. As an auditor, I want the current Relationship Version, so that I can see the current proposal.
4. As an auditor, I want linked record identifiers, so that I can understand the relationship.
5. As an auditor, I want the rationale, so that I can understand why the relationship was proposed.
6. As an auditor, I want source support, so that I can trace the proposal to its sources.
7. As an auditor, I want gaps and contradictions, so that I can see review risks.
8. As an auditor, I want earlier decisions, so that I can see the decision history.
9. As an auditor, I want live updates, so that the screen shows current fictional data.
10. As a reviewer, I want only fictional data, so that G0 remains effective.
11. As a reviewer, I want immutable version and decision records, so that history remains traceable.
12. As a developer, I want isolated development and preview data, so that environments cannot share records.
13. As a developer, I want strict validators and indexes, so that invalid or slow queries do not deploy.
14. As a developer, I want a preview URL for each pull request, so that changes can be checked before merge.
15. As the user, I want the Python workbench unchanged, so that the pilot cannot disrupt approved work.
16. As the user, I want a bounded pilot, so that the first slice stays small and reversible.

## Implementation Decisions

- Build a new isolated TypeScript web application module.
- Do not replace or edit the current Python workbench in this pilot.
- Use Next.js and a small set of shadcn interface components.
- Use Convex as the only backend for the pilot application.
- Use one Convex schema for fictional Engagement, Relationship Review, Relationship Version and Auditor Decision records.
- Use strict validators for every Convex query, mutation and return value.
- Use indexes for every query path.
- Do not use table scans or unbounded collection reads.
- Provide one public queue query and one public item query.
- Provide one internal seed mutation for fictional records.
- Do not provide public write, approval or decision mutations.
- Mark every seeded Engagement as fictional.
- Block every record that is not fictional before it reaches a public query result.
- Use fictional identifiers and descriptions only.
- Do not import, upload or synchronise data from the Python workbench.
- Use separate Convex development and preview deployments.
- Use Vercel Git integration for pull request preview deployments.
- Protect the preview deployment from general public access.
- Do not create a production release in this pilot.
- Keep Vercel Functions out of the pilot unless Next.js needs a framework route.
- Keep business data and Relationship Review rules in Convex.
- Treat a preview head change as a new validation candidate.

## Testing Decisions

- Test the queue query through its public result.
- Test the item query through its public result.
- Test that non-fictional records do not appear.
- Test immutable Relationship Version and Auditor Decision records.
- Test queue ordering and item links.
- Test empty, missing and blocked states.
- Run TypeScript type checking.
- Run the application lint command.
- Push the Convex schema and functions to an isolated deployment.
- Run one realistic Convex query smoke test.
- Run the Next.js production build.
- Check the Vercel preview through the browser.
- Confirm the preview uses its isolated Convex deployment.
- Run the complete pilot test suite after the last change.
- Run Pocock code-review against this specification.
- Obtain Fresh Sol review after final validation.

## Out Of Scope

- Real client information.
- Changes to G0.
- DeepSec.
- Australian data-location assessment.
- Convex or Vercel exit planning.
- Convex or Vercel cost assessment.
- An adopt, defer or reject decision.
- Production deployment.
- Authenticated approval or decision actions.
- Evidence capture or file upload.
- Migration from SQLite.
- Synchronisation with the Python workbench.
- Mobile or offline operation.

## Further Notes

The Convex quickstart scaffold is not suitable for this pilot.

That scaffold is local-only and has no authentication or Vercel publishing.

Use a standard Convex and Vercel setup after the implementation plan receives approval.
