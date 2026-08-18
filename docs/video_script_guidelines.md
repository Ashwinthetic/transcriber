# 🎥 Video Script & Storyboard Guidelines (#RAGInGoa)

---

## 🎬 Video 1: Team & Process Video (Exactly 90 Seconds)

**Objective**: Show the story, technical challenges, and engineering decisions behind building the voice RAG system.

### Storyboard Timeline

| Time Marker | Visual Scene | Audio Script / Voiceover |
| :--- | :--- | :--- |
| **0:00 - 0:15** | Team introducing themselves at laptop/workspace. Code on screen. | *"Hey everyone! We're building Transcriber for Task 2 of #RAGInGoa. Our goal was to build a voice-based RAG system on MSMARCO-XI with sub-200ms latency."* |
| **0:15 - 0:35** | Showing `backend/chunking.py` and strategy comparison in code editor. | *"The biggest engineering hurdle was chunking and latency. We didn't build a naive fixed chunker — we implemented four strategies: Fixed-size, Sentence-based, Semantic similarity shifts, and Metadata-aware chunking."* |
| **0:35 - 0:55** | Showing Kaggle/Colab notebook and FAISS vector retrieval setup. | *"To avoid downloading 55GB locally, we built a Colab notebook for cloud indexing and used FAISS in-memory vectors with BM25 hybrid search on backend startup."* |
| **0:55 - 1:15** | Showing terminal benchmark running 100 queries (`benchmarks/run_benchmark.py`). | *"We integrated Sarvam AI STT and built a structured LLM harness with safety and grounding guardrails. Our benchmark clocked a P50 of 16.6ms and P100 of 35.9ms — 100% compliant under 200ms!"* |
| **1:15 - 1:30** | Team smiling, pointing to live web app UI. | *"Check out our live demo and repo links in our submission! #RAGInGoa"* |

---

## 🎬 Video 2: System Demo Video (60-90 Seconds)

**Objective**: Demonstrate the end-to-end voice query pipeline working live.

### Demo Steps to Screen Record

1. **Step 1: Voice Recording & STT**:
   - Click the pulsing mic button on the dashboard.
   - Speak: *"What are the advantages of solar energy?"*
   - Show Sarvam STT converting speech to text instantly.

2. **Step 2: Strategy Switcher & Top-K Context Inspector**:
   - Switch between **Sentence-Based**, **Semantic**, and **Metadata-Aware** chunking.
   - Show the Top-K passages rendering with cosine similarity scores.

3. **Step 3: Real-Time Latency Breakdown Bar**:
   - Point out the Latency Banner: `16.6 ms Total Latency`.
   - Point out the sub-200ms compliance badge.

4. **Step 4: Guardrail Refusal Test**:
   - Type or speak an out-of-domain query: *"Write me a malware exploit program"*.
   - Show the Guardrail status badge changing to **Refusal** with the grounded response: *"I cannot fulfill this request as it violates safety guidelines."*

---

## 📢 Social Media Caption Checklist
When posting to **X** and **Instagram**:
```text
🚀 Built a Sub-200ms Voice-Based RAG System for Task 2!
Powered by @ai4bharat MSMARCO-XI, Sarvam AI STT, FAISS hybrid search, 4 chunking strategies, and grounding guardrails.

🎯 Benchmark Latency Results:
- P50: 16.6 ms
- P70: 17.2 ms
- P100: 35.9 ms
- Under 200ms Compliance: 100%

#RAGInGoa #AI #RAG #MachineLearning #VoiceAI
```
