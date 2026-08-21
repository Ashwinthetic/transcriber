"use client";

import { useRef, useState } from "react";
import { UploadCloud, Mic, Music, X, Play, Pause, RefreshCw } from "lucide-react";
import { useSTTStore } from "@/store/useSTTStore";
import Image from "next/image";

export function DropZone() {
  const {
    audioFile,
    audioUrl,
    audioName,
    setAudioFile,
    clearAudio,
    openRecordingModal,
    isTranscribing,
  } = useSTTStore();

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setAudioFile(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setAudioFile(file);
    }
  };

  const togglePlayback = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  return (
    <div className="w-full">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="audio/*,.mp3,.wav,.m4a,.flac,.ogg"
        className="hidden"
      />

      {/* Main Container */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative glass-card border-dashed rounded-3xl p-8 transition-all flex flex-col items-center justify-center text-center ${
          isDragOver
            ? "border-black bg-white/90 shadow-2xl scale-[1.02]"
            : "border-white/60 hover:border-white hover:shadow-lg"
        } ${isTranscribing ? "opacity-75 pointer-events-none" : ""}`}
      >
        {isTranscribing && (
          <div className="absolute inset-0 bg-white/80 backdrop-blur-sm rounded-3xl z-10 flex flex-col items-center justify-center gap-3">
            <RefreshCw className="w-8 h-8 text-black animate-spin" />
            <p className="text-sm font-semibold text-[#111111]">
              Transcribing audio with HHGOA Speech Engine...
            </p>
          </div>
        )}

        {!audioFile ? (
          <>
            {/* Upload Icon */}
            <div className="mb-6 relative w-24 h-24 drop-shadow-md">
              <Image src="/assets/hhgoa/140-frame-1948755145-54-27273.svg" alt="Upload Art" fill className="object-contain mix-blend-multiply" />
            </div>

            <h3 className="text-base font-bold text-[#111111] mb-1">
              Drag and drop or click to upload
            </h3>
            <p className="text-xs text-gray-400 mb-6">
              Audio file, up to 100 MB or 1 hour (MP3, WAV, M4A, FLAC)
            </p>

            <div className="flex items-center gap-4 flex-wrap justify-center">
              {/* Upload Button */}
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-6 py-2.5 bg-[#111111] text-white rounded-full text-xs font-semibold hover:bg-black transition-colors shadow-subtle flex items-center gap-2"
              >
                <UploadCloud className="w-3.5 h-3.5" />
                Upload File
              </button>

              <span className="text-xs font-medium text-gray-400">or</span>

              {/* Record Audio Button */}
              <button
                onClick={openRecordingModal}
                className="px-6 py-2.5 bg-[#FAFAFA] border border-[#E5E5E5] text-[#111111] rounded-full text-xs font-semibold hover:bg-[#F3F4F6] transition-colors flex items-center gap-2"
              >
                <Mic className="w-3.5 h-3.5 text-[#FF6B00]" />
                Record Audio
              </button>
            </div>
          </>
        ) : (
          /* Loaded Audio State */
          <div className="w-full max-w-lg bg-[#FAFAFA] border border-[#E5E5E5] rounded-2xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="w-10 h-10 rounded-xl bg-white border border-[#E5E5E5] flex items-center justify-center shrink-0">
                <Music className="w-5 h-5 text-[#FF6B00]" />
              </div>
              <div className="text-left overflow-hidden">
                <p className="text-xs font-bold text-[#111111] truncate max-w-[200px] sm:max-w-[280px]">
                  {audioName}
                </p>
                <p className="text-[10px] text-gray-400">Audio Ready for Transcription</p>
              </div>
            </div>

            {audioUrl && (
              <audio
                ref={audioRef}
                src={audioUrl}
                onEnded={() => setIsPlaying(false)}
                className="hidden"
              />
            )}

            <div className="flex items-center gap-2">
              <button
                onClick={togglePlayback}
                className="p-2.5 rounded-full bg-[#111111] text-white hover:bg-black transition-colors"
                title={isPlaying ? "Pause" : "Play Preview"}
              >
                {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
              </button>

              <button
                onClick={clearAudio}
                className="p-2.5 rounded-full bg-white border border-[#E5E5E5] text-gray-500 hover:text-red-600 hover:border-red-200 transition-colors"
                title="Remove Audio"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
