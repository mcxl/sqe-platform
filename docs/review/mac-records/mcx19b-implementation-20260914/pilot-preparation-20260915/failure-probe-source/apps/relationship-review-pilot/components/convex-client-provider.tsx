"use client";

import { ConvexProvider, ConvexReactClient } from "convex/react";
import { useState, type ReactNode } from "react";

export function ConvexClientProvider({
  children,
  url,
}: {
  children: ReactNode;
  url: string;
}) {
  const [client] = useState(() => new ConvexReactClient(url));

  return <ConvexProvider client={client}>{children}</ConvexProvider>;
}
