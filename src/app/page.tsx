"use client";

import { Sidebar } from "@/components/Sidebar";
import { TopBar } from "@/components/TopBar";
import { DropZone } from "@/components/DropZone";
import { ConfigRow } from "@/components/ConfigRow";
import { ResultPanel } from "@/components/ResultPanel";
import { TryExamples } from "@/components/TryExamples";
import { AudioRecordModal } from "@/components/AudioRecordModal";
import { HistoryDrawer } from "@/components/HistoryDrawer";
import { FeedbackModal } from "@/components/FeedbackModal";
import { useSTTStore } from "@/store/useSTTStore";
import { AlertCircle } from "lucide-react";

import Image from "next/image";

export default function MainPage() {
  const { error } = useSTTStore();

  return (
    <div className="min-h-screen text-white flex flex-row relative overflow-hidden">
      {/* Global HHGOA Theme Background */}
      <div className="fixed inset-0 z-[-2]">
        <Image
          src="/assets/hhgoa/Sun rise.png"
          alt="HHGOA Sunrise Background"
          fill
          priority
          className="object-cover object-center opacity-80"
        />
        <div className="absolute inset-0 bg-white/20 backdrop-blur-[2px]" />
      </div>

      {/* Footer Trees Overlay */}
      <div className="fixed bottom-0 left-0 w-full z-[-1] pointer-events-none opacity-90 mix-blend-multiply">
        <Image
          src="/assets/hhgoa/footer trees.png"
          alt="HHGOA Footer Trees"
          width={1920}
          height={400}
          className="w-full object-cover object-bottom"
        />
      </div>

      {/* Left Sidebar */}
      <Sidebar />

      {/* Main Content Workspace */}
      <div className="flex-1 flex flex-col min-w-0 z-10 overflow-y-auto">
        {/* Top Header Bar */}
        <TopBar />

        {/* Page Main Panel */}
        <main className="flex-1 p-4 lg:p-8 max-w-6xl w-full mx-auto relative z-10 pb-32">
          {error && (
            <div className="mb-6 p-4 bg-red-50/90 backdrop-blur-md border border-red-200 text-red-700 rounded-2xl text-xs font-semibold flex items-center gap-2 shadow-lg">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
              <span>{error}</span>
            </div>
          )}

          {/* 1. Large Audio Drop Zone & Record Trigger */}
          <DropZone />

          {/* 2. Configuration Options Row */}
          <ConfigRow />

          {/* 3. Result Panel (Transcription + LLM Post-Processing) */}
          <ResultPanel />

          {/* 4. Try Some Examples Section */}
          <TryExamples />
        </main>

        <footer className="py-6 text-center text-xs text-white/60 font-semibold glass-topbar mt-auto relative z-10">
          HHGOA Content Agent Engine · Sub-200ms Voice Pipeline · #RAGInGoa
        </footer>
      </div>

      {/* Modals & Drawers */}
      <AudioRecordModal />
      <HistoryDrawer />
      <FeedbackModal />
    </div>
  );
}
