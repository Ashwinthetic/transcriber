"use client";

import { useState } from "react";
import { MessageSquare, X, Send, Check } from "lucide-react";
import { useSTTStore } from "@/store/useSTTStore";

export function FeedbackModal() {
  const { isFeedbackOpen, toggleFeedback } = useSTTStore();
  const [feedback, setFeedback] = useState("");
  const [sent, setSent] = useState(false);

  if (!isFeedbackOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSent(true);
    setTimeout(() => {
      setSent(false);
      setFeedback("");
      toggleFeedback();
    }, 1500);
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-xs z-50 flex items-center justify-center p-4">
      <div className="bg-white border border-[#E5E5E5] rounded-3xl w-full max-w-md p-6 shadow-float relative animate-in fade-in zoom-in-95">
        <div className="flex items-center justify-between pb-4 border-b border-[#E5E5E5]">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-[#FF6B00]" />
            <h3 className="font-bold text-base text-[#111111] font-heading">
              Feedback & Insights
            </h3>
          </div>
          <button
            onClick={toggleFeedback}
            className="p-1 rounded-full text-gray-400 hover:text-black hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {sent ? (
          <div className="py-12 flex flex-col items-center justify-center text-center">
            <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mb-3">
              <Check className="w-6 h-6" />
            </div>
            <h4 className="font-bold text-[#111111] text-base">Thank You!</h4>
            <p className="text-xs text-gray-500 mt-1">
              Your feedback helps us refine the HHGOA Speech-to-Text Content Agent tool.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="py-4 space-y-4">
            <p className="text-xs text-gray-600">
              How was your transcription experience? Share feature requests, language accuracy notes, or general feedback with the HHGOA team.
            </p>

            <textarea
              rows={4}
              required
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Type your feedback here..."
              className="w-full p-3 bg-[#FAFAFA] border border-[#E5E5E5] rounded-2xl text-xs text-[#111111] focus:outline-none focus:ring-2 focus:ring-black focus:bg-white transition-all"
            />

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={toggleFeedback}
                className="px-4 py-2 bg-[#FAFAFA] border border-[#E5E5E5] text-xs font-semibold rounded-xl text-gray-700 hover:bg-gray-100"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-5 py-2 bg-[#111111] text-white text-xs font-semibold rounded-xl hover:bg-black transition-colors flex items-center gap-1.5 shadow-subtle"
              >
                <Send className="w-3.5 h-3.5" />
                Submit
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
