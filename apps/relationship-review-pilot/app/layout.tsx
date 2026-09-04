import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Relationship Review Pilot",
  description: "Read-only fictional relationship review pilot.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en-AU">
      <body>{children}</body>
    </html>
  );
}
