import type { Metadata } from "next";
import "./globals.css";
import { AppProvider } from "../context/AppContext";
import ClientLayout from "./ClientLayout";

export const metadata: Metadata = {
  title: "Transcriber AI — Voice-Enabled RAG Studio",
  description:
    "Sub-200ms Voice RAG pipeline powered by Sarvam AI saaras:v3 STT, FAISS Vector DB, and MSMARCO-XI knowledge base. Built for HH Goa 2026.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <AppProvider>
          <ClientLayout>{children}</ClientLayout>
        </AppProvider>
      </body>
    </html>
  );
}
