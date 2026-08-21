import { create } from "zustand";

export interface STTResult {
  transcript: string;
  detectedLanguage: string;
  confidence: number;
  llmOutput?: string;
  modelUsed: string;
  processedAt: string;
}

export interface HistoryItem extends STTResult {
  id: string;
  fileName: string;
  duration?: string;
}

interface STTState {
  // Audio state
  audioFile: File | Blob | null;
  audioUrl: string | null;
  audioName: string | null;
  exampleId: string | null;

  // Recording Modal state
  isRecordingModalOpen: boolean;

  // Config state
  selectedModel: string;
  selectedLanguage: string;
  selectedLLM: string;

  // Processing & Result state
  isTranscribing: boolean;
  result: STTResult | null;
  editedTranscript: string;
  error: string | null;

  // History state
  history: HistoryItem[];
  isHistoryOpen: boolean;

  // Feedback modal
  isFeedbackOpen: boolean;

  // Actions
  setAudioFile: (file: File | Blob | null, name?: string, url?: string) => void;
  clearAudio: () => void;
  openRecordingModal: () => void;
  closeRecordingModal: () => void;
  setSelectedModel: (model: string) => void;
  setSelectedLanguage: (lang: string) => void;
  setSelectedLLM: (llm: string) => void;
  setEditedTranscript: (text: string) => void;
  toggleHistory: () => void;
  toggleFeedback: () => void;

  loadExample: (example: {
    title: string;
    language: string;
    exampleId: string;
    sampleText: string;
  }) => void;

  runTranscription: () => Promise<void>;
}

export const useSTTStore = create<STTState>((set, get) => ({
  audioFile: null,
  audioUrl: null,
  audioName: null,
  exampleId: null,

  isRecordingModalOpen: false,

  selectedModel: "hhgoa-stt-v1",
  selectedLanguage: "Hindi",
  selectedLLM: "None",

  isTranscribing: false,
  result: null,
  editedTranscript: "",
  error: null,

  history: [],
  isHistoryOpen: false,
  isFeedbackOpen: false,

  setAudioFile: (file, name, customUrl) => {
    const existingUrl = get().audioUrl;
    if (existingUrl && existingUrl.startsWith("blob:")) {
      URL.revokeObjectURL(existingUrl);
    }

    if (!file) {
      set({ audioFile: null, audioUrl: null, audioName: null, exampleId: null, result: null });
      return;
    }

    const url = customUrl || (file ? URL.createObjectURL(file as Blob) : null);
    const fileName = name || (file && "name" in file ? (file as File).name : "recorded_audio.wav");

    set({
      audioFile: file,
      audioUrl: url,
      audioName: fileName,
      exampleId: null,
      error: null,
    });
  },

  clearAudio: () => {
    const existingUrl = get().audioUrl;
    if (existingUrl && existingUrl.startsWith("blob:")) {
      URL.revokeObjectURL(existingUrl);
    }
    set({
      audioFile: null,
      audioUrl: null,
      audioName: null,
      exampleId: null,
      result: null,
      editedTranscript: "",
      error: null,
    });
  },

  openRecordingModal: () => set({ isRecordingModalOpen: true }),
  closeRecordingModal: () => set({ isRecordingModalOpen: false }),

  setSelectedModel: (selectedModel) => set({ selectedModel }),
  setSelectedLanguage: (selectedLanguage) => set({ selectedLanguage }),
  setSelectedLLM: (selectedLLM) => set({ selectedLLM }),
  setEditedTranscript: (editedTranscript) => set({ editedTranscript }),

  toggleHistory: () => set((state) => ({ isHistoryOpen: !state.isHistoryOpen })),
  toggleFeedback: () => set((state) => ({ isFeedbackOpen: !state.isFeedbackOpen })),

  loadExample: (example) => {
    const fakeBlob = new Blob([example.sampleText], { type: "audio/wav" });
    const url = URL.createObjectURL(fakeBlob);
    set({
      audioFile: fakeBlob,
      audioUrl: url,
      audioName: `${example.title}.wav`,
      selectedLanguage: example.language,
      exampleId: example.exampleId,
      result: null,
      editedTranscript: "",
      error: null,
    });
  },

  runTranscription: async () => {
    const { audioFile, selectedModel, selectedLanguage, selectedLLM, exampleId, audioName } = get();

    if (!audioFile) {
      set({ error: "Please upload or record audio first." });
      return;
    }

    set({ isTranscribing: true, error: null });

    try {
      const formData = new FormData();
      formData.append("file", audioFile, audioName || "audio.wav");
      formData.append("model", selectedModel);
      formData.append("language", selectedLanguage);
      if (exampleId) formData.append("exampleId", exampleId);

      const response = await fetch("/api/stt", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to process speech to text.");
      }

      const sttData = await response.json();

      let llmOutput = "";
      if (selectedLLM !== "None") {
        const llmRes = await fetch("/api/llm-postprocess", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            transcript: sttData.transcript,
            llmOption: selectedLLM,
            targetLanguage: selectedLanguage,
          }),
        });
        if (llmRes.ok) {
          const llmData = await llmRes.json();
          llmOutput = llmData.llmOutput;
        }
      }

      const resultObj: STTResult = {
        transcript: sttData.transcript,
        detectedLanguage: sttData.detectedLanguage,
        confidence: sttData.confidence,
        llmOutput: llmOutput || undefined,
        modelUsed: sttData.modelUsed,
        processedAt: sttData.processedAt,
      };

      const historyEntry: HistoryItem = {
        ...resultObj,
        id: `hist_${Date.now()}`,
        fileName: audioName || "Audio clip",
      };

      set((state) => ({
        isTranscribing: false,
        result: resultObj,
        editedTranscript: sttData.transcript,
        history: [historyEntry, ...state.history],
      }));
    } catch (err: any) {
      set({
        isTranscribing: false,
        error: err.message || "An error occurred during transcription.",
      });
    }
  },
}));
