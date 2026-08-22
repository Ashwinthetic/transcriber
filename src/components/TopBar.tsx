"use client";

import { History, MessageSquare, Sparkles } from "lucide-react";
import { useSTTStore } from "@/store/useSTTStore";
import Image from "next/image";

export function TopBar() {
  const { toggleHistory, toggleFeedback, history } = useSTTStore();

  return (
    <header className="h-16 glass-topbar px-4 lg:px-8 flex items-center justify-between sticky top-0 z-20">
      {/* Title */}
      <div className="flex items-center gap-3">
        <h1 className="text-xl font-bold font-heading text-white flex items-center gap-2">
          Speech to Text
          <Image src="/assets/hhgoa/036-vector-54-3934.svg" alt="Decorative Vector" width={32} height={32} className="drop-shadow-[0_0_12px_rgba(255,223,0,1)] brightness-[1.4]" />
        </h1>
        <span className="hidden sm:inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-white/10 border border-white/20 text-[11px] font-semibold text-white">
          <Sparkles className="w-3 h-3 text-[#FF6B00]" />
          hhgoa v1.0
        </span>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-2">
        <button
          onClick={toggleHistory}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl border border-white/20 bg-white/5 text-xs font-semibold text-white hover:bg-white/10 transition-colors relative"
        >
          <History className="w-3.5 h-3.5" />
          <span>History</span>
          {history.length > 0 && (
            <span className="w-4 h-4 rounded-full bg-[#111111] text-white text-[10px] flex items-center justify-center font-bold">
              {history.length}
            </span>
          )}
        </button>

        <button
          onClick={toggleFeedback}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl border border-white/20 bg-white/5 text-xs font-semibold text-white hover:bg-white/10 transition-colors"
        >
          <MessageSquare className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Feedback</span>
        </button>
      </div>
    </header>
  );
}
