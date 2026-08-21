import { NextRequest, NextResponse } from "next/server";
export async function POST(req: NextRequest) {

  try {
    const formData = await req.formData();
    const file = formData.get("file") as File | null;
    const model = (formData.get("model") as string) || "hhgoa-stt-v1";
    const language = (formData.get("language") as string) || "Hindi";
    const exampleId = formData.get("exampleId") as string | null;

    // Simulate real-world network & processing delay
    await new Promise((resolve) => setTimeout(resolve, 1400));

    // TODO: replace with real STT provider call (e.g. Sarvam AI STT API / Whisper API)
    let transcript = "";
    let detectedLanguage = language;
    let confidence = 0.98;

    if (exampleId === "ex-1" || language === "Hindi") {
      transcript =
        "नमस्कार! हैकर हाउस गोवा २०२६ में आपका स्वागत है। हम यहाँ एक उच्च गति और कम विलंबता वाला स्पीच-टू-टेक्स्ट इंजन बना रहे हैं। यह सिस्टम कंटेंट एजेंट्स को रियल-टाइम में ऑडियो को सटीक टेक्स्ट में बदलने में सक्षम बनाता है।";
      detectedLanguage = "Hindi";
    } else if (exampleId === "ex-3" || language === "Konkani") {
      transcript =
        "देव बोरों दीस दिवो! हॅकर हाउस गोंय २०२६ खातीर तुमचे येवकार आसा. आमी गोंयांत भारत देशान्तल्या सगळ्यांत व्हडल्या बिल्डरांक एकत्र हाडून नवीं तंत्रज्ञानां तयार करतांव.";
      detectedLanguage = "Konkani";
    } else {
      transcript =
        "Welcome to Hacker House Goa 2026! We are building the next generation of voice-enabled content agents powered by HHGOA's high-speed Speech-to-Text inference pipeline. Designed for low latency, sub-200ms processing, and multi-lingual precision across English, Hindi, and regional languages.";
      detectedLanguage = "English";
    }

    if (file) {
      const fileName = file.name || "recorded_audio.wav";
      if (!exampleId) {
        transcript = `[Transcribed from ${fileName} via ${model}] ` + transcript;
      }
    }

    return NextResponse.json({
      transcript,
      detectedLanguage,
      confidence,
      modelUsed: model,
      processedAt: new Date().toISOString(),
    });
  } catch (error) {
    console.error("STT Processing Error:", error);
    return NextResponse.json(
      { error: "Failed to process audio transcription." },
      { status: 500 }
    );
  }
}
