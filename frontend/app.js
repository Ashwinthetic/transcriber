document.addEventListener('DOMContentLoaded', () => {
  // DOM References
  const micBtn = document.getElementById('micBtn');
  const micRing = document.getElementById('micRing');
  const micCaption = document.getElementById('micCaption');
  const waveformCanvas = document.getElementById('waveformCanvas');

  const sttProviderSelect = document.getElementById('sttProviderSelect');
  const langSelect = document.getElementById('langSelect');
  const stratPills = document.querySelectorAll('.strat-pill');
  const textQueryInput = document.getElementById('textQueryInput');
  const btnExecuteRAG = document.getElementById('btnExecuteRAG');
  const qtChips = document.querySelectorAll('.qt-chip');

  // Results DOM
  const p50Val = document.getElementById('p50Val');
  const p70Val = document.getElementById('p70Val');
  const p100Val = document.getElementById('p100Val');
  const complianceVal = document.getElementById('complianceVal');

  const totLatDisplay = document.getElementById('totLatDisplay');
  const targetCompliantBadge = document.getElementById('targetCompliantBadge');
  const valStt = document.getElementById('valStt');
  const valRet = document.getElementById('valRet');
  const valGuard = document.getElementById('valGuard');
  const valLlm = document.getElementById('valLlm');

  const barStt = document.getElementById('barStt');
  const barRet = document.getElementById('barRet');
  const barGuard = document.getElementById('barGuard');
  const barLlm = document.getElementById('barLlm');

  const transcriptTextDisplay = document.getElementById('transcriptTextDisplay');
  const sttMetaTag = document.getElementById('sttMetaTag');
  const answerBodyText = document.getElementById('answerBodyText');
  const guardrailBadge = document.getElementById('guardrailBadge');
  const activeStratBadge = document.getElementById('activeStratBadge');
  const chunksListContainer = document.getElementById('chunksListContainer');

  // State
  let activeStrategy = 'sentence_based';
  let activeSttProvider = 'sarvam';
  let activeLang = 'en-IN';
  let isRecording = false;
  let mediaRecorder = null;
  let audioChunks = [];

  // Canvas context for audio wave
  const ctx = waveformCanvas ? waveformCanvas.getContext('2d') : null;
  let animId = null;

  // 1. Draw Waveform Visualizer
  function drawWaveform(isSpeaking = false) {
    if (!ctx) return;
    ctx.clearRect(0, 0, waveformCanvas.width, waveformCanvas.height);
    const bars = 30;
    const barWidth = 4;
    const gap = 6;
    const startX = (waveformCanvas.width - (bars * (barWidth + gap))) / 2;

    for (let i = 0; i < bars; i++) {
      const x = startX + i * (barWidth + gap);
      const height = isSpeaking ? Math.sin(Date.now() * 0.01 + i) * 18 + 22 : 4;
      const gradient = ctx.createLinearGradient(0, 0, 0, waveformCanvas.height);
      gradient.addColorStop(0, '#6366f1');
      gradient.addColorStop(1, '#06b6d4');
      ctx.fillStyle = gradient;
      ctx.fillRect(x, (waveformCanvas.height - height) / 2, barWidth, height);
    }
    if (isSpeaking) {
      animId = requestAnimationFrame(() => drawWaveform(true));
    }
  }
  drawWaveform(false);

  // 2. Fetch Benchmark Metrics
  async function loadBenchmarkData() {
    try {
      const res = await fetch('/api/benchmark');
      if (res.ok) {
        const data = await res.json();
        p50Val.textContent = `${data.P50_ms} ms`;
        p70Val.textContent = `${data.P70_ms} ms`;
        p100Val.textContent = `${data.P100_ms} ms`;
        complianceVal.textContent = `${data.under_200ms_percentage}%`;
      }
    } catch (e) {
      console.warn("Could not load benchmark metrics:", e);
    }
  }
  loadBenchmarkData();

  // 3. Strategy Switcher
  stratPills.forEach(pill => {
    pill.addEventListener('click', () => {
      stratPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      activeStrategy = pill.getAttribute('data-strategy');
      activeStratBadge.textContent = activeStrategy;
    });
  });

  // 4. Select Dropdowns
  sttProviderSelect.addEventListener('change', (e) => {
    activeSttProvider = e.target.value;
    sttMetaTag.textContent = activeSttProvider === 'sarvam' ? 'Sarvam saaras:v3' : 'ElevenLabs STT';
  });

  langSelect.addEventListener('change', (e) => {
    activeLang = e.target.value;
  });

  // 5. Topic Chips
  qtChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const q = chip.getAttribute('data-q');
      textQueryInput.value = q;
      runQueryPipeline(q);
    });
  });

  // 6. Mic Trigger
  micBtn.addEventListener('click', () => {
    if (!isRecording) {
      startRecording();
    } else {
      stopRecording();
    }
  });

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunks.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = () => {
          const b64 = reader.result.split(',')[1];
          runQueryPipeline(null, b64);
        };
      };

      mediaRecorder.start();
      isRecording = true;
      micRing.classList.add('recording');
      micCaption.textContent = "Listening... Click mic to finish recording";
      drawWaveform(true);
    } catch (err) {
      console.warn("Mic access blocked or unsupported:", err);
      micCaption.textContent = "Mic unavailable. Running prompt query...";
      runQueryPipeline(textQueryInput.value || "What are the advantages of solar energy?");
    }
  }

  function stopRecording() {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      isRecording = false;
      micRing.classList.remove('recording');
      micCaption.textContent = "Transcribing audio via Sarvam AI saaras:v3...";
      if (animId) cancelAnimationFrame(animId);
      drawWaveform(false);
    }
  }

  // 7. Execute Button
  btnExecuteRAG.addEventListener('click', () => {
    const q = textQueryInput.value.trim();
    if (q) runQueryPipeline(q);
  });

  textQueryInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      const q = textQueryInput.value.trim();
      if (q) runQueryPipeline(q);
    }
  });

  // 8. Pipeline Execution API Call
  async function runQueryPipeline(queryText = null, base64Audio = null) {
    btnExecuteRAG.disabled = true;
    answerBodyText.innerHTML = "⚡ <em>Executing Voice RAG pipeline... (Sarvam STT ➔ FAISS ➔ Guardrail ➔ LLM)</em>";

    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: queryText,
          audio_base64: base64Audio,
          strategy: activeStrategy,
          stt_provider: activeSttProvider,
          top_k: 3
        })
      });

      if (!res.ok) throw new Error("Query API error");

      const data = await res.json();
      renderResponse(data);
    } catch (err) {
      console.error(err);
      answerBodyText.textContent = "Error communicating with backend.";
    } finally {
      btnExecuteRAG.disabled = false;
      micCaption.textContent = "Click microphone button to record voice prompt";
    }
  }

  // 9. Render Pipeline Results
  function renderResponse(data) {
    // Total Latency & Compliance Badge
    const tot = data.total_latency_ms;
    totLatDisplay.textContent = tot.toFixed(1);

    if (data.latency_target_met) {
      targetCompliantBadge.innerHTML = '<span class="pulse-dot-green"></span> Sub-200ms Target Passed';
      targetCompliantBadge.style.background = 'rgba(16, 185, 129, 0.15)';
      targetCompliantBadge.style.color = '#34d399';
    } else {
      targetCompliantBadge.innerHTML = '⚠️ Over 200ms Target';
      targetCompliantBadge.style.background = 'rgba(245, 158, 11, 0.15)';
      targetCompliantBadge.style.color = '#fbbf24';
    }

    // Breakdown Values
    valStt.textContent = data.stt_latency_ms.toFixed(1);
    valRet.textContent = data.retrieval_latency_ms.toFixed(1);
    valGuard.textContent = data.guardrail_latency_ms.toFixed(1);
    valLlm.textContent = data.llm_latency_ms.toFixed(1);

    const sum = (data.stt_latency_ms + data.retrieval_latency_ms + data.guardrail_latency_ms + data.llm_latency_ms) || 1;
    barStt.style.width = `${(data.stt_latency_ms / sum) * 100}%`;
    barRet.style.width = `${(data.retrieval_latency_ms / sum) * 100}%`;
    barGuard.style.width = `${(data.guardrail_latency_ms / sum) * 100}%`;
    barLlm.style.width = `${(data.llm_latency_ms / sum) * 100}%`;

    // Transcript
    transcriptTextDisplay.textContent = `"${data.query}"`;

    // Answer & Guardrail Badge
    answerBodyText.textContent = data.answer;
    if (data.grounded) {
      guardrailBadge.innerHTML = '🛡️ Grounding Score: ' + (data.grounding_score * 100).toFixed(0) + '%';
      guardrailBadge.style.background = 'rgba(16, 185, 129, 0.2)';
      guardrailBadge.style.color = '#34d399';
    } else {
      guardrailBadge.innerHTML = '🛑 Refusal Refutation';
      guardrailBadge.style.background = 'rgba(244, 63, 94, 0.2)';
      guardrailBadge.style.color = '#f43f5e';
    }

    // Top-K Chunks
    chunksListContainer.innerHTML = '';
    if (data.retrieved_chunks && data.retrieved_chunks.length > 0) {
      data.retrieved_chunks.forEach((chunk, i) => {
        const item = document.createElement('div');
        item.className = 'chunk-item';
        const sim = (chunk.similarity_score !== undefined) ? chunk.similarity_score.toFixed(4) : 'N/A';
        const title = chunk.title || chunk.doc_id || `Passage #${i+1}`;
        item.innerHTML = `
          <div class="ci-meta">
            <span>[#${i+1}] ${title}</span>
            <span>FAISS Cosine Sim: ${sim}</span>
          </div>
          <div class="ci-text">${chunk.text}</div>
        `;
        chunksListContainer.appendChild(item);
      });
    } else {
      chunksListContainer.innerHTML = '<div class="empty-state">No context passages met grounding threshold.</div>';
    }
  }
});
