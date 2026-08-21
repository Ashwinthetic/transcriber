"use client";

import { useEffect, useRef, useState } from "react";
import { Mic, Square, X, Check, RefreshCw } from "lucide-react";
import { useSTTStore } from "@/store/useSTTStore";

export function AudioRecordModal() {
  const { isRecordingModalOpen, closeRecordingModal, setAudioFile } = useSTTStore();

  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!isRecordingModalOpen) {
      handleReset();
    }
  }, [isRecordingModalOpen]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        setRecordedBlob(audioBlob);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start(100);
      setIsRecording(true);
      setRecordingTime(0);

      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      alert("Microphone access denied or not supported in browser.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) clearInterval(timerRef.current);
    }
  };

  const handleReset = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
    setRecordingTime(0);
    setRecordedBlob(null);
  };

  const handleSaveRecordedClip = () => {
    if (recordedBlob) {
      const file = new File([recordedBlob], `recording_${Date.now()}.wav`, {
        type: "audio/wav",
      });
      setAudioFile(file);
      closeRecordingModal();
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  if (!isRecordingModalOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white border border-[#E5E5E5] rounded-3xl w-full max-w-md p-6 shadow-float relative animate-in fade-in zoom-in-95">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-[#E5E5E5]">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-[#FAFAFA] border border-[#E5E5E5] flex items-center justify-center">
              <Mic className="w-4 h-4 text-[#FF6B00]" />
            </div>
            <h3 className="font-bold font-heading text-[#111111] text-base">
              Record Audio
            </h3>
          </div>
          <button
            onClick={closeRecordingModal}
            className="p-1 rounded-full text-gray-400 hover:text-black hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Dynamic Visualizer Body */}
        <div className="py-8 flex flex-col items-center justify-center">
          {/* Waveform Bars */}
          <div className="h-16 flex items-center gap-1.5 justify-center mb-6 w-full px-8">
            {[40, 70, 30, 90, 50, 80, 40, 100, 60, 30, 85, 45, 95, 35, 75].map(
              (height, idx) => (
                <div
                  key={idx}
                  style={{
                    height: isRecording ? `${height}%` : "20%",
                    animationDelay: `${idx * 0.08}s`,
                  }}
                  className={`w-1.5 rounded-full transition-all duration-200 ${
                    isRecording
                      ? "bg-[#FF6B00] animate-wave-bar"
                      : recordedBlob
                      ? "bg-black"
                      : "bg-gray-200"
                  }`}
                />
              )
            )}
          </div>

          {/* Timer Display */}
          <div className="text-3xl font-bold font-heading text-[#111111] mb-2 tracking-tight">
            {formatTime(recordingTime)}
          </div>
          <p className="text-xs text-gray-400">
            {isRecording
              ? "Recording live audio..."
              : recordedBlob
              ? "Audio clip captured! Click save to load into drop zone."
              : "Click record to start capture"}
          </p>
        </div>

        {/* Actions Footer */}
        <div className="flex items-center gap-3 pt-4 border-t border-[#E5E5E5]">
          {!isRecording && !recordedBlob && (
            <button
              onClick={startRecording}
              className="w-full py-3 bg-[#111111] text-white rounded-xl text-xs font-semibold hover:bg-black transition-colors flex items-center justify-center gap-2 shadow-subtle"
            >
              <Mic className="w-4 h-4 text-[#FF6B00]" />
              Start Recording
            </button>
          )}

          {isRecording && (
            <button
              onClick={stopRecording}
              className="w-full py-3 bg-red-600 text-white rounded-xl text-xs font-semibold hover:bg-red-700 transition-colors flex items-center justify-center gap-2 shadow-subtle"
            >
              <Square className="w-4 h-4 fill-white" />
              Stop Recording
            </button>
          )}

          {!isRecording && recordedBlob && (
            <>
              <button
                onClick={handleReset}
                className="flex-1 py-2.5 bg-[#FAFAFA] border border-[#E5E5E5] text-[#111111] rounded-xl text-xs font-semibold hover:bg-gray-100 transition-colors flex items-center justify-center gap-1.5"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Retake
              </button>
              <button
                onClick={handleSaveRecordedClip}
                className="flex-1 py-2.5 bg-[#111111] text-white rounded-xl text-xs font-semibold hover:bg-black transition-colors flex items-center justify-center gap-1.5 shadow-subtle"
              >
                <Check className="w-3.5 h-3.5" />
                Load Clip
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
