import type { HTMLAttributes } from "react";
import { cn } from "./utils";

export function Skeleton({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      data-slot="skeleton"
      className={cn("animate-pulse rounded-md bg-slate-200", className)}
      {...props}
    />
  );
}
