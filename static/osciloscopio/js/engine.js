/* =============================================
   ENGINE.JS — Motor de renderização do Canvas
   ============================================= */

const OscEngine = (() => {
  let canvas, ctx, W, H;

  const WORLD = { xMin: -2, xMax: 2, yMin: -5, yMax: 5 };

  let pontosDica   = [];
  let estadoAtual  = { A: 0, B: 1, C: 1, D: 0, tipoFunc: 'sen' };
  let animFrame    = null;
  let tick         = 0;
  let vitoria      = false;
  let sonarIdx     = 0;

  // Sonar timing (frames @ ~60fps)
  const SONAR_FADE_IN  = 25;
  const SONAR_HOLD     = 90;
  const SONAR_FADE_OUT = 25;
  const SONAR_GAP      = 20;   // pausa escura entre pontos
  const SONAR_CYCLE    = SONAR_FADE_IN + SONAR_HOLD + SONAR_FADE_OUT + SONAR_GAP;

  function wx(x) { return (x - WORLD.xMin) / (WORLD.xMax - WORLD.xMin) * W; }
  function wy(y) { return (1 - (y - WORLD.yMin) / (WORLD.yMax - WORLD.yMin)) * H; }

  // ── Grade ────────────────────────────────────────────────
  function desenharGrade() {
    ctx.save();

    // Linhas menores a cada 0.5
    ctx.strokeStyle = 'rgba(51,255,51,0.09)';
    ctx.lineWidth = 1;
    for (let x = WORLD.xMin; x <= WORLD.xMax + 0.001; x += 0.5) {
      ctx.beginPath(); ctx.moveTo(wx(x), 0); ctx.lineTo(wx(x), H); ctx.stroke();
    }
    for (let y = WORLD.yMin; y <= WORLD.yMax + 0.001; y += 1) {
      ctx.beginPath(); ctx.moveTo(0, wy(y)); ctx.lineTo(W, wy(y)); ctx.stroke();
    }

    // Eixos centrais
    ctx.strokeStyle = 'rgba(51,255,51,0.30)';
    ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(0, wy(0)); ctx.lineTo(W, wy(0)); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(wx(0), 0); ctx.lineTo(wx(0), H); ctx.stroke();

    // Rótulos
    ctx.fillStyle = 'rgba(51,180,51,0.5)';
    ctx.font = `${Math.max(9, W * 0.022)}px "Share Tech Mono", monospace`;
    ctx.textAlign = 'center';
    for (let x = WORLD.xMin; x <= WORLD.xMax; x += 0.5) {
      if (x !== 0 && x % 1 === 0) ctx.fillText(x, wx(x), wy(0) + 13);
    }
    ctx.textAlign = 'right';
    for (let y = WORLD.yMin; y <= WORLD.yMax; y += 1) {
      if (y !== 0) ctx.fillText(y, wx(0) - 5, wy(y) + 4);
    }
    ctx.restore();
  }

  // ── Onda ─────────────────────────────────────────────────
  function f(x, A, B, C, D, tipo) {
    const arg = C * Math.PI * x + D;
    return A + B * (tipo === 'sen' ? Math.sin(arg) : Math.cos(arg));
  }

  function desenharOnda(A, B, C, D, tipo) {
    if (B <= 0 || C <= 0) return;
    ctx.save();
    const cor = vitoria ? '#ffff66' : '#33ff33';
    ctx.strokeStyle = cor;
    ctx.lineWidth = vitoria ? 3 : 2;
    ctx.shadowBlur = vitoria ? 22 : 12;
    ctx.shadowColor = vitoria ? '#ffffaa' : '#33ff33';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    for (let px = 0; px <= W; px++) {
      const x = WORLD.xMin + (px / W) * (WORLD.xMax - WORLD.xMin);
      const cy = wy(f(x, A, B, C, D, tipo));
      if (px === 0) ctx.moveTo(px, cy); else ctx.lineTo(px, cy);
    }
    ctx.stroke();
    ctx.restore();
  }

  // ── Sonar: um ponto por vez com fade ─────────────────────
  function desenharSonar() {
    if (vitoria || pontosDica.length === 0) return;

    const frame = tick % SONAR_CYCLE;

    // Avança ponto ao iniciar novo ciclo e dispara ping sonoro
    if (frame === 0 && tick > 0) {
      sonarIdx = (sonarIdx + 1) % pontosDica.length;
    }
    // Ping no momento exato em que o ponto começa a aparecer (frame 0 do fade-in)
    if (frame === 0 && typeof OscAudio !== 'undefined') {
      const proxPonto = pontosDica[sonarIdx];
      if (proxPonto) OscAudio.sonarPing(proxPonto.tipo);
    }

    // Calcula alpha do ciclo atual
    let alpha = 0;
    if (frame < SONAR_FADE_IN) {
      alpha = frame / SONAR_FADE_IN;
    } else if (frame < SONAR_FADE_IN + SONAR_HOLD) {
      alpha = 1;
    } else if (frame < SONAR_FADE_IN + SONAR_HOLD + SONAR_FADE_OUT) {
      alpha = 1 - (frame - SONAR_FADE_IN - SONAR_HOLD) / SONAR_FADE_OUT;
    } else {
      return; // gap — sem desenho
    }

    const p = pontosDica[sonarIdx];
    const px = wx(p.x);
    const py = wy(p.y);
    const cores = { max: '#ff6633', min: '#44aaff', zero: '#ffcc00' };
    const cor = cores[p.tipo] || '#ffffff';

    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.shadowColor = cor;
    ctx.strokeStyle = cor;
    ctx.fillStyle = cor;

    // Cruz
    const s = 7;
    ctx.lineWidth = 2;
    ctx.shadowBlur = 14;
    ctx.beginPath();
    ctx.moveTo(px - s, py - s); ctx.lineTo(px + s, py + s);
    ctx.moveTo(px + s, py - s); ctx.lineTo(px - s, py + s);
    ctx.stroke();

    // Anel pulsante
    const pulse = 1 + 0.25 * Math.sin(tick * 0.18);
    ctx.globalAlpha = alpha * 0.35;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(px, py, (s + 6) * pulse, 0, Math.PI * 2);
    ctx.stroke();

    // Ponto central
    ctx.globalAlpha = alpha;
    ctx.shadowBlur = 8;
    ctx.beginPath();
    ctx.arc(px, py, 3, 0, Math.PI * 2);
    ctx.fill();

    // Texto: tipo + coordenadas
    ctx.globalAlpha = alpha * 0.85;
    ctx.shadowBlur = 5;
    const label = p.tipo === 'max' ? '▲ MAX' : p.tipo === 'min' ? '▼ MIN' : '○ ZERO';
    const fontSize = Math.max(9, W * 0.022);
    ctx.font = `${fontSize}px "Share Tech Mono", monospace`;
    ctx.textAlign = 'left';
    ctx.fillText(label, px + s + 5, py + 3);
    ctx.globalAlpha = alpha * 0.55;
    ctx.font = `${Math.max(8, W * 0.018)}px "Share Tech Mono", monospace`;
    ctx.fillText(`(${p.x.toFixed(2)}, ${p.y.toFixed(2)})`, px + s + 5, py + fontSize + 4);

    ctx.restore();
  }

  // ── Loop ─────────────────────────────────────────────────
  function loop() {
    tick++;

    // Verifica resize dinâmico
    const rect = canvas.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0) {
      const dpr = devicePixelRatio || 1;
      const tw = Math.floor(rect.width * dpr);
      const th = Math.floor(rect.height * dpr);
      if (canvas.width !== tw || canvas.height !== th) {
        canvas.width  = tw;
        canvas.height = th;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        W = rect.width;
        H = rect.height;
      }
    }

    ctx.clearRect(0, 0, W, H);

    // Fundo CRT verde-escuro
    ctx.fillStyle = '#001100';
    ctx.fillRect(0, 0, W, H);

    // Vinheta radial
    const grd = ctx.createRadialGradient(W / 2, H / 2, H * 0.15, W / 2, H / 2, W * 0.7);
    grd.addColorStop(0, 'rgba(0,10,0,0)');
    grd.addColorStop(1, 'rgba(0,0,0,0.5)');
    ctx.fillStyle = grd;
    ctx.fillRect(0, 0, W, H);

    desenharGrade();
    desenharSonar();

    const { A, B, C, D, tipoFunc } = estadoAtual;
    desenharOnda(A, B, C, D, tipoFunc);

    animFrame = requestAnimationFrame(loop);
  }

  // ── Resize inicial ───────────────────────────────────────
  function resize() {
    const rect = canvas.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;
    const dpr = devicePixelRatio || 1;
    canvas.width  = Math.floor(rect.width  * dpr);
    canvas.height = Math.floor(rect.height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    W = rect.width;
    H = rect.height;
  }

  return {
    init(canvasEl, dicas) {
      canvas = canvasEl;
      ctx = canvas.getContext('2d');
      pontosDica = dicas || [];
      // Aguarda o DOM renderizar para pegar dimensões reais
      requestAnimationFrame(() => {
        resize();
        window.addEventListener('resize', resize);
      });
    },
    atualizar(estado) {
      estadoAtual = { ...estado };
    },
    setVitoria(v) {
      vitoria = v;
    },
    iniciarLoop() {
      if (animFrame) cancelAnimationFrame(animFrame);
      loop();
    },
    parar() {
      if (animFrame) cancelAnimationFrame(animFrame);
    }
  };
})();