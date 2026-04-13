import type { ReactNode } from "react";
import type { Metadata } from "next";
import "./theme.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "FPDS Admin",
  description: "FPDS admin console login and overview"
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body className="fpds-admin-body">{children}</body>
    </html>
  );
}
