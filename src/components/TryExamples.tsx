"use client";

import { Mic, Radio, Award, Play } from "lucide-react";
import { useSTTStore } from "@/store/useSTTStore";

export function TryExamples() {
  const { loadExample } = useSTTStore();

  const examples = [
    {
      exampleId: "ex-1",
      icon: Award,
      title: "HH Goa Hackathon Pitch",
      description: "Sample speech explaining the low-latency Voice RAG engine built at Hacker House Goa.",
      language: "Hindi",
      sampleText: "नमस्कार! हैकर हाउस गोवा २०२६ में आपका स्वागत है। हम यहाँ एक उच्च गति और कम विलंबता वाला स्पीच-टू-टेक्स्ट इंजन बना रहे हैं।",
    },
    {
      exampleId: "ex-2",
      icon: Radio,
      title: "Technical Architecture Overview",
      description: "Sub-200ms speech inference architecture benchmarked across FAISS and LLM harness.",
      language: "English",
      sampleText: "Welcome to Hacker House Goa 2026! We are building the next generation of voice-enabled content agents powered by HHGOA's high-speed Speech-to-Text inference pipeline.",
    },
    {
      exampleId: "ex-3",
      icon: Mic,
      title: "Konkani Cultural Announcement",
      description: "Goan regional language audio clip demonstrating native dialect recognition.",
      language: "Konkani",
      sampleText: "देव बोरों दीस दिवो! हॅकर हाउस गोंय २०२६ खातीर तुमचे येवकार आसा. आमी गोंयांत भारत देशान्तल्या सगळ्यांत व्हडल्या बिल्डरांक एकत्र हाडून नवीं तंत्रज्ञानां तयार करतांव.",
    },
  ];

  return (
    <div className="my-8">
      <h3 className="text-sm font-bold text-[#111111] uppercase tracking-wider mb-4 flex items-center gap-2 drop-shadow-sm">
        <span>Try Some Examples</span>
        <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-white/60 backdrop-blur-sm border border-white/50 text-gray-800 shadow-sm">
          Click to load sample
        </span>
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {examples.map((ex) => {
          const Icon = ex.icon;
          return (
            <div
              key={ex.exampleId}
              onClick={() => loadExample(ex)}
              className="glass-card rounded-3xl p-5 hover:border-black hover:bg-white/90 transition-all cursor-pointer group shadow-subtle flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="w-9 h-9 rounded-2xl bg-white/50 border border-white/60 flex items-center justify-center group-hover:bg-[#111111] transition-colors shadow-sm">
                    <Icon className="w-4 h-4 text-[#111111] group-hover:text-white transition-colors" />
                  </div>
                  <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-white/50 border border-white/60 text-[#111111] shadow-sm">
                    {ex.language}
                  </span>
                </div>

                <h4 className="font-bold text-sm text-[#111111] mb-1 font-heading group-hover:text-black">
                  {ex.title}
                </h4>
                <p className="text-xs text-gray-500 line-clamp-2 leading-relaxed">
                  {ex.description}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-white/60 flex items-center justify-between text-xs font-semibold text-gray-800 group-hover:text-black">
                <span>Load Sample</span>
                <Play className="w-3.5 h-3.5 fill-current" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
