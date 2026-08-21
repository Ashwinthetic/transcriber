"use client";

import { useState } from "react";
import { Copy, Download, Check, Sparkles, Languages, CheckCircle2 } from "lucide-react";
import { useSTTStore } from "@/store/useSTTStore";

export function ResultPanel() {
  const { result, editedTranscript, setEditedTranscript } = useSTTStore();
  const [copied, setCopied] = useState(false);

  if (!result) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(editedTranscript || result.transcript);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const textToDownload = `HHGOA SPEECH-TO-TEXT TRANSCRIPT
Processed: ${result.processedAt}
Model: ${result.modelUsed}
Detected Language: ${result.detectedLanguage}
Confidence: ${(result.confidence * 100).toFixed(1)}%

--- TRANSCRIPT ---
${editedTranscript || result.transcript}

${result.llmOutput ? `\n--- LLM POST-PROCESSING OUTPUT ---\n${result.llmOutput}` : ""}`;

    const blob = new Blob([textToDownload], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `hhgoa_transcript_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 my-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
      {/* Main Transcript Card */}
      <div className="glass-card rounded-3xl p-6 shadow-card">
        {/* Header Badges & Controls */}
        <div className="flex flex-wrap items-center justify-between gap-3 pb-4 mb-4 border-b border-white/60">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/50 border border-white/60 text-xs font-semibold text-[#111111]">
              <Languages className="w-3.5 h-3.5 text-[#FF6B00]" />
              Detected: <strong className="text-black">{result.detectedLanguage}</strong>
            </span>

            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-medium">
              <CheckCircle2 className="w-3.5 h-3.5" />
              {(result.confidence * 100).toFixed(0)}% Confidence
            </span>

            <span className="text-xs text-gray-400 font-mono">
              {result.modelUsed}
            </span>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="px-3.5 py-1.5 bg-white/50 border border-white/60 text-[#111111] rounded-xl text-xs font-semibold hover:bg-white/80 transition-colors flex items-center gap-1.5"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
              {copied ? "Copied!" : "Copy"}
            </button>

            <button
              onClick={handleDownload}
              className="px-3.5 py-1.5 bg-[#111111] text-white rounded-xl text-xs font-semibold hover:bg-black transition-colors flex items-center gap-1.5 shadow-subtle"
            >
              <Download className="w-3.5 h-3.5" />
              Download
            </button>
          </div>
        </div>

        {/* Editable Transcript Textarea */}
        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Editable Transcript
          </label>
          <textarea
            rows={5}
            value={editedTranscript}
            onChange={(e) => setEditedTranscript(e.target.value)}
            className="w-full p-4 bg-white/40 border border-white/60 rounded-2xl text-sm text-[#111111] leading-relaxed font-normal focus:outline-none focus:ring-2 focus:ring-black focus:bg-white/70 transition-all resize-y"
            placeholder="Transcribed text will appear here..."
          />
        </div>
      </div>

      {/* Secondary Card for LLM Output (if selected) */}
      {result.llmOutput && (
        <div className="glass-card rounded-3xl p-6 shadow-card border-l-4 border-l-purple-600">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-7 h-7 rounded-lg bg-purple-50 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-purple-600" />
            </div>
            <h4 className="font-bold text-sm text-[#111111] font-heading">
              LLM Post-Processing Output
            </h4>
          </div>

          <div className="p-4 bg-white/40 border border-white/60 rounded-2xl text-xs text-[#111111] leading-relaxed font-mono whitespace-pre-wrap">
            {result.llmOutput}
          </div>
        </div>
      )}
    </div>
  );
}
