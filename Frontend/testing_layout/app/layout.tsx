import type { Metadata } from "next";
import "./globals.css";


export const metadata: Metadata = {
  title: "Transit Dashboard",
  description: "Go Transit real-time intelligence",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
