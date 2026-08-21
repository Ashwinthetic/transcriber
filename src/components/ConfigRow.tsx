"use client";

import { Cpu, Globe, Sparkles, Zap } from "lucide-react";
import { useSTTStore } from "@/store/useSTTStore";

export function ConfigRow() {
  const {
    selectedModel,
    setSelectedModel,
    selectedLanguage,
    setSelectedLanguage,
    selectedLLM,
    setSelectedLLM,
    runTranscription,
    isTranscribing,
    audioFile,
  } = useSTTStore();

  return (
    <div className="glass-card rounded-3xl p-5 shadow-subtle my-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5">
        {/* 1. STT Model Selector */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-white" />
            STT Model
          </label>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-black/40 border border-white/20 rounded-xl text-xs font-semibold text-white focus:outline-none focus:ring-2 focus:ring-white/50 cursor-pointer transition-all"
          >
            <option value="hhgoa-stt-v1">hhgoa-stt-v1 (High Accuracy)</option>
            <option value="hhgoa-stt-fast">hhgoa-stt-fast (Sub-200ms)</option>
            <option value="hhgoa-stt-pro">hhgoa-stt-pro (Multi-Speaker)</option>
          </select>
        </div>

        {/* 2. Native Language Selector */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider flex items-center gap-1.5">
            <Globe className="w-3.5 h-3.5 text-[#FF6B00]" />
            Native Language
          </label>
          <select
            value={selectedLanguage}
            onChange={(e) => setSelectedLanguage(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-black/40 border border-white/20 rounded-xl text-xs font-semibold text-white focus:outline-none focus:ring-2 focus:ring-white/50 cursor-pointer transition-all"
          >
            <option value="Hindi">Hindi (हिंदी)</option>
            <option value="English">English (US/IN)</option>
            <option value="Konkani">Konkani (कोंकणी)</option>
            <option value="Marathi">Marathi (मराठी)</option>
          </select>
        </div>

        {/* 3. LLM Post-Processing Selector */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            LLM Post-Processing
          </label>
          <select
            value={selectedLLM}
            onChange={(e) => setSelectedLLM(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-black/40 border border-white/20 rounded-xl text-xs font-semibold text-white focus:outline-none focus:ring-2 focus:ring-white/50 cursor-pointer transition-all"
          >
            <option value="None">None (Raw Transcript)</option>
            <option value="hhgoa-llm-summarize">hhgoa-llm-summarize (Key Points)</option>
            <option value="hhgoa-llm-translate">hhgoa-llm-translate (English)</option>
          </select>
        </div>
      </div>

      {/* Action Button */}
      <div className="flex items-center justify-between pt-2 border-t border-white/20">
        <div className="text-xs text-gray-400 font-medium">
          {audioFile ? (
            <span className="text-emerald-600 font-semibold flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Audio loaded & ready
            </span>
          ) : (
            "Select or record audio to enable transcription"
          )}
        </div>

        <button
          onClick={runTranscription}
          disabled={!audioFile || isTranscribing}
          className="px-8 py-3 bg-white text-black font-bold rounded-2xl text-xs hover:bg-gray-200 transition-all shadow-subtle disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <Zap className="w-4 h-4 fill-black text-black" />
          {isTranscribing ? "Processing..." : "Transcribe"}
        </button>
      </div>
    </div>
  );
}
