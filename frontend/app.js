document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const micButton = document.getElementById('micButton');
  const micStatusText = document.getElementById('micStatusText');
  const queryInput = document.getElementById('queryInput');
  const btnSubmitQuery = document.getElementById('btnSubmitQuery');
  const strategyBtns = document.querySelectorAll('.strategy-btn');
  const sttRadioPills = document.querySelectorAll('.radio-pill input[name="stt_provider"]');
  const sampleChips = document.querySelectorAll('.chip');

  // Latency & Results DOM
  const totalLatencyNum = document.getElementById('totalLatencyNum');
  const targetBadgeStatus = document.getElementById('targetBadgeStatus');
  const sttLatVal = document.getElementById('sttLatVal');
  const retLatVal = document.getElementById('retLatVal');
  const guardLatVal = document.getElementById('guardLatVal');
  const llmLatVal = document.getElementById('llmLatVal');
  
  const segStt = document.getElementById('segStt');
  const segRet = document.getElementById('segRet');
  const segGuard = document.getElementById('segGuard');
  const segLlm = document.getElementById('segLlm');

  const answerOutputText = document.getElementById('answerOutputText');
  const guardPill = document.getElementById('guardPill');
  const activeStrategyTag = document.getElementById('activeStrategyTag');
  const chunksContainer = document.getElementById('chunksContainer');

  // Benchmark Metrics DOM
  const p50Value = document.getElementById('p50Value');
  const p70Value = document.getElementById('p70Value');
  const p100Value = document.getElementById('p100Value');
  const complianceValue = document.getElementById('complianceValue');

  // App State & API Configuration
  const API_BASE = (window.location.protocol.startsWith('http') && (window.location.port === '8000' || window.location.port === ''))
    ? ''
    : 'http://127.0.0.1:8000';

  let activeStrategy = 'sentence_based';
  let activeSttProvider = 'sarvam';
  let isRecording = false;
  let mediaRecorder = null;
  let audioChunks = [];

  // 1. Fetch Benchmark Stats on load
  async function loadBenchmarkStats() {
    try {
      const res = await fetch(`${API_BASE}/api/benchmark`);
      if (res.ok) {
        const data = await res.json();
        p50Value.textContent = `${data.P50_ms} ms`;
        p70Value.textContent = `${data.P70_ms} ms`;
        p100Value.textContent = `${data.P100_ms} ms`;
        complianceValue.textContent = `${data.under_200ms_percentage}%`;
      }
    } catch (e) {
      console.warn("Could not load benchmark stats from backend:", e);
    }
  }
  loadBenchmarkStats();

  // 2. Strategy Switching Handler
  strategyBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      strategyBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeStrategy = btn.getAttribute('data-strategy');
      activeStrategyTag.textContent = activeStrategy;
    });
  });

  // 3. STT Provider Handler
  sttRadioPills.forEach(radio => {
    radio.addEventListener('change', (e) => {
      document.querySelectorAll('.radio-pill').forEach(p => p.classList.remove('active'));
      e.target.closest('.radio-pill').classList.add('active');
      activeSttProvider = e.target.value;
    });
  });

  // 4. Sample Query Chips Handler
  sampleChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const q = chip.getAttribute('data-query');
      queryInput.value = q;
      executeQuery(q);
    });
  });

  // 5. Mic Audio Recorder
  micButton.addEventListener('click', async () => {
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

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = () => {
          const base64Audio = reader.result.split(',')[1];
          executeQuery(null, base64Audio);
        };
      };

      mediaRecorder.start();
      isRecording = true;
      micButton.classList.add('recording');
      micStatusText.textContent = "Listening... Click to stop recording";
    } catch (err) {
      console.warn("Microphone access unavailable or denied. Using fast prompt encoder:", err);
      micStatusText.textContent = "Mic access blocked. Using fast audio prompt fallback...";
      executeQuery(queryInput.value || "What are the advantages of solar energy?");
    }
  }

  function stopRecording() {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      isRecording = false;
      micButton.classList.remove('recording');
      micStatusText.textContent = "Processing audio transcription...";
    }
  }

  // 6. Submit Query Button Handler
  btnSubmitQuery.addEventListener('click', () => {
    const q = queryInput.value.trim();
    if (q) executeQuery(q);
  });

  queryInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      const q = queryInput.value.trim();
      if (q) executeQuery(q);
    }
  });

  // 7. Execute Query Pipeline API Call
  async function executeQuery(textQuery = null, base64Audio = null) {
    btnSubmitQuery.disabled = true;
    answerOutputText.innerHTML = "⚡ <em>Processing Voice RAG Pipeline...</em>";

    try {
      const payload = {
        query: textQuery,
        audio_base64: base64Audio,
        strategy: activeStrategy,
        stt_provider: activeSttProvider,
        top_k: 3
      };

      const res = await fetch(`${API_BASE}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);

      const data = await res.json();
      renderQueryResponse(data);
    } catch (err) {
      console.error("Query Execution Error:", err);
      answerOutputText.innerHTML = `⚠️ <strong>Connection Notice:</strong> Unable to connect to backend (${err.message}).<br><br>Please make sure the backend server is running on <code>http://127.0.0.1:8000</code>.`;
    } finally {
      btnSubmitQuery.disabled = false;
      micStatusText.textContent = "Click mic to record voice prompt";
    }
  }

  // 8. Render Response & Latency Metrics
  function renderQueryResponse(data) {
    // Total Latency & Target Badge
    const tot = data.total_latency_ms;
    totalLatencyNum.textContent = tot.toFixed(1);

    if (data.latency_target_met) {
      targetBadgeStatus.textContent = "⚡ < 200ms Target Passed";
      targetBadgeStatus.style.background = "rgba(16, 185, 129, 0.2)";
      targetBadgeStatus.style.color = "#34d399";
    } else {
      targetBadgeStatus.textContent = "⚠️ Over 200ms";
      targetBadgeStatus.style.background = "rgba(245, 158, 11, 0.2)";
      targetBadgeStatus.style.color = "#fbbf24";
    }

    // Pipeline Breakdown Values
    sttLatVal.textContent = data.stt_latency_ms.toFixed(1);
    retLatVal.textContent = data.retrieval_latency_ms.toFixed(1);
    guardLatVal.textContent = data.guardrail_latency_ms.toFixed(1);
    llmLatVal.textContent = data.llm_latency_ms.toFixed(1);

    // Update Progress Bar Proportions
    const sum = (data.stt_latency_ms + data.retrieval_latency_ms + data.guardrail_latency_ms + data.llm_latency_ms) || 1;
    segStt.style.width = `${(data.stt_latency_ms / sum) * 100}%`;
    segRet.style.width = `${(data.retrieval_latency_ms / sum) * 100}%`;
    segGuard.style.width = `${(data.guardrail_latency_ms / sum) * 100}%`;
    segLlm.style.width = `${(data.llm_latency_ms / sum) * 100}%`;

    // Render Answer & Guardrail Pill
    answerOutputText.textContent = data.answer;
    if (data.grounded) {
      guardPill.textContent = "Grounding Score: " + (data.grounding_score * 100).toFixed(0) + "%";
      guardPill.style.background = "rgba(16, 185, 129, 0.2)";
      guardPill.style.color = "#34d399";
    } else {
      guardPill.textContent = "Refusal Refutation";
      guardPill.style.background = "rgba(244, 63, 94, 0.2)";
      guardPill.style.color = "#f43f5e";
    }

    // Render Top-K Chunks
    chunksContainer.innerHTML = '';
    if (data.retrieved_chunks && data.retrieved_chunks.length > 0) {
      data.retrieved_chunks.forEach((chunk, i) => {
        const div = document.createElement('div');
        div.className = 'chunk-card';
        const simScore = (chunk.similarity_score !== undefined) ? chunk.similarity_score.toFixed(4) : "N/A";
        const title = chunk.title || chunk.doc_id || `Passage #${i+1}`;
        div.innerHTML = `
          <div class="chunk-meta">
            <span>[#${i+1}] ${title}</span>
            <span>Cosine Sim: ${simScore}</span>
          </div>
          <div class="chunk-body">${chunk.text}</div>
        `;
        chunksContainer.appendChild(div);
      });
    } else {
      chunksContainer.innerHTML = '<div class="empty-state">No context passages met grounding threshold.</div>';
    }
  }
});
