import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "Stoic Companion · A little perspective",
  description:
    "Reflect on everyday life with verified passages from the Stoics.",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
