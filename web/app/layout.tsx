import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "StoreSignal AI — Voice-of-Store Engine",
  description:
    "Multilingual retail operations intelligence: early-warning and incident-resolution, not a sentiment dashboard.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <div aria-hidden className="app-atmosphere" />
        {children}
      </body>
    </html>
  );
}
