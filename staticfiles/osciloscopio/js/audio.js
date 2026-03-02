/* =============================================
   AUDIO.JS — Sons sintéticos via Web Audio API
   ============================================= */

const OscAudio = (() => {
  let ctx = null;
  let inicializado = false;
  let ultimoValKnob = {};   // evita repetir beep no mesmo valor

  // ── Inicializa o AudioContext no primeiro gesto do usuário ──
  function init() {
    if (inicializado) return;
    ctx = new (window.AudioContext || window.webkitAudioContext)();
    inicializado = true;
  }

  // ── Primitiva de beep ────────────────────────────────────────
  // Cria oscilador → gain → destino com envelope ADSR simplificado
  function beep({ freq = 440, tipo = 'sine', duracao = 0.15, volume = 0.25,
                  attack = 0.005, decay = 0.05, detune = 0 } = {}) {
    if (!ctx) return;
    const now  = ctx.currentTime;
    const osc  = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.type            = tipo;
    osc.frequency.value = freq;
    osc.detune.value    = detune;

    // Envelope: attack → sustain → decay para o final
    gain.gain.setValueAtTime(0, now);
    gain.gain.linearRampToValueAtTime(volume, now + attack);
    gain.gain.setValueAtTime(volume, now + attack + decay);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + duracao);

    osc.start(now);
    osc.stop(now + duracao + 0.01);
  }

  // ── Ruído branco (estática de rádio) ─────────────────────────
  function noise({ duracao = 0.12, volume = 0.08 } = {}) {
    if (!ctx) return;
    const bufSize   = ctx.sampleRate * duracao;
    const buffer    = ctx.createBuffer(1, bufSize, ctx.sampleRate);
    const data      = buffer.getChannelData(0);
    for (let i = 0; i < bufSize; i++) data[i] = Math.random() * 2 - 1;

    const source = ctx.createBufferSource();
    source.buffer = buffer;

    const gain = ctx.createGain();
    // Filtro passa-banda para dar textura de rádio
    const filter = ctx.createBiquadFilter();
    filter.type            = 'bandpass';
    filter.frequency.value = 1200;
    filter.Q.value         = 0.8;

    source.connect(filter);
    filter.connect(gain);
    gain.connect(ctx.destination);

    const now = ctx.currentTime;
    gain.gain.setValueAtTime(volume, now);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + duracao);

    source.start(now);
    source.stop(now + duracao + 0.01);
  }

  // ══════════════════════════════════════════
  //  SONS SEMÂNTICOS DO JOGO
  // ══════════════════════════════════════════

  // Toca ao girar qualquer knob (um tick por mudança de valor inteiro)
  function knobTick(valor) {
    if (!ctx) return;
    // Frequência varia com o valor para dar feedback posicional
    const freq = 220 + Math.abs(valor) * 55;
    beep({ freq, tipo: 'square', duracao: 0.04, volume: 0.08, attack: 0.002, decay: 0.01 });
    // Estática curta sobreposta para textura mecânica
    noise({ duracao: 0.03, volume: 0.04 });
  }

  // Toca quando o ponto sonar aparece na tela
  function sonarPing(tipo) {
    if (!ctx) return;
    // Frequência diferente por tipo de ponto crítico
    const freqs = { max: 1320, min: 660, zero: 880 };
    const freq  = freqs[tipo] || 880;
    beep({ freq, tipo: 'sine', duracao: 0.25, volume: 0.12, attack: 0.008, decay: 0.03 });
    // Eco sutil (delay simulado com segundo oscilador atrasado)
    setTimeout(() => {
      beep({ freq: freq * 0.5, tipo: 'sine', duracao: 0.2, volume: 0.04, attack: 0.01 });
    }, 80);
  }

  // Toca ao trocar entre SEN e COS
  function trocarFuncao() {
    if (!ctx) return;
    beep({ freq: 660, tipo: 'triangle', duracao: 0.08, volume: 0.15, attack: 0.003 });
    setTimeout(() => {
      beep({ freq: 880, tipo: 'triangle', duracao: 0.08, volume: 0.10, attack: 0.003 });
    }, 70);
  }

  // Jingle de vitória — sequência de notas ascendente
  function vitoria() {
    if (!ctx) return;

    // Escala pentatônica em Lá maior: A4, C#5, E5, A5, C#6
    const notas = [440, 554, 659, 880, 1108];
    const DELAY = 130; // ms entre notas

    notas.forEach((freq, i) => {
      setTimeout(() => {
        beep({ freq, tipo: 'sine', duracao: 0.35, volume: 0.22, attack: 0.01, decay: 0.05 });
        // Harmônico de suporte
        beep({ freq: freq * 1.5, tipo: 'triangle', duracao: 0.25, volume: 0.07, attack: 0.01 });
      }, i * DELAY);
    });

    // Nota final sustentada + ruído de "sinal interceptado"
    setTimeout(() => {
      beep({ freq: 1108, tipo: 'sine', duracao: 0.8, volume: 0.18, attack: 0.02, decay: 0.1 });
      noise({ duracao: 0.4, volume: 0.06 });
    }, notas.length * DELAY + 50);
  }

  return { init, knobTick, sonarPing, trocarFuncao, vitoria };
})();