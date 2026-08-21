"use client";

import { X, History, Trash2, FileText } from "lucide-react";
import { useSTTStore } from "@/store/useSTTStore";

export function HistoryDrawer() {
  const { isHistoryOpen, toggleHistory, history, setEditedTranscript } = useSTTStore();

  if (!isHistoryOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 flex justify-end">
      <div className="w-full max-w-md bg-[#111111] h-full border-l border-white/20 p-6 shadow-float flex flex-col justify-between animate-in slide-in-from-right duration-200">
        <div>
          {/* Header */}
          <div className="flex items-center justify-between pb-4 border-b border-white/20 mb-4">
            <div className="flex items-center gap-2">
              <History className="w-5 h-5 text-[#FF6B00]" />
              <h3 className="font-bold text-base text-white font-heading">
                Transcription History
              </h3>
            </div>
            <button
              onClick={toggleHistory}
              className="p-1 rounded-full text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* History Item List */}
          <div className="space-y-3 max-h-[75vh] overflow-y-auto pr-1">
            {history.length === 0 ? (
              <div className="text-center py-12 text-gray-400 text-xs">
                No past transcriptions recorded in this session yet.
              </div>
            ) : (
              history.map((item) => (
                <div
                  key={item.id}
                  onClick={() => setEditedTranscript(item.transcript)}
                  className="p-4 bg-white/10 border border-white/20 rounded-2xl hover:border-white/40 transition-colors cursor-pointer"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-bold text-white truncate max-w-[200px]">
                      {item.fileName}
                    </span>
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-white/10 border border-white/20 text-white">
                      {item.detectedLanguage}
                    </span>
                  </div>
                  <p className="text-xs text-gray-300 line-clamp-2 leading-relaxed">
                    {item.transcript}
                  </p>
                  <div className="mt-2 pt-2 border-t border-white/20 flex items-center justify-between text-[10px] text-gray-400">
                    <span>{new Date(item.processedAt).toLocaleTimeString()}</span>
                    <span>{item.modelUsed}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <button
          onClick={toggleHistory}
          className="w-full py-2.5 bg-white text-black rounded-xl text-xs font-semibold hover:bg-gray-200 transition-colors mt-4"
        >
          Close History
        </button>
      </div>
    </div>
  );
}
