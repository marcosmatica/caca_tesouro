/* =============================================
   CONTROLES.JS — Knobs, lógica do jogo, UI
   ============================================= */

document.addEventListener('DOMContentLoaded', () => {

  // ── Dados injetados pelo Django ──────────────────────────
  const NIVEL       = JSON.parse(document.getElementById('nivel-data').textContent);
  const PONTOS_DICA = JSON.parse(document.getElementById('pontos-dica-data').textContent);
  const VERIFICAR_URL = document.getElementById('verificar-url').value;

  // ── Estado inicial do usuário ────────────────────────────
  const estado = { A: 0, B: 1, C: 1, D: 0, tipoFunc: 'sen' };

  // ── Config dos parâmetros ────────────────────────────────
  const PARAMS = {
    A: { min: -4, max:  4, label: 'DESL. VERT.' },
    B: { min:  1, max:  5, label: 'AMPLITUDE'   },
    C: { min:  1, max:  4, label: 'FREQUÊNCIA'  },
    D: { min:  0, max:  6, label: 'FASE'        },
  };

  // ── Inicializa Canvas ────────────────────────────────────
  const canvas = document.getElementById('oscCanvas');
  OscEngine.init(canvas, PONTOS_DICA);
  OscEngine.atualizar({ ...estado });
  OscEngine.iniciarLoop();

  // ── Inicializa áudio no primeiro gesto (requisito do browser) ──
  let audioIniciado = false;
  function garantirAudio() {
    if (!audioIniciado) { OscAudio.init(); audioIniciado = true; }
  }
  document.addEventListener('mousedown', garantirAudio, { once: true });
  document.addEventListener('touchstart', garantirAudio, { once: true });

  // ── Ângulo de rotação visual do knob ────────────────────
  // -135° = mínimo, +135° = máximo
  function anguloPara(val, cfg) {
    return -135 + ((val - cfg.min) / (cfg.max - cfg.min)) * 270;
  }

  // ── Cria um knob interativo ───────────────────────────────
  function criarKnob(param) {
    const cfg     = PARAMS[param];
    const grupo   = document.getElementById(`knob-group-${param}`);
    if (!grupo) return;
    const knobEl  = grupo.querySelector('.knob');
    const valEl   = grupo.querySelector('.knob-value');

    // Renderiza estado atual
    function aplicar(v) {
      v = Math.max(cfg.min, Math.min(cfg.max, Math.round(v)));
      estado[param] = v;
      valEl.textContent = v >= 0 ? '+' + v : String(v);
      knobEl.style.transform = `rotate(${anguloPara(v, cfg)}deg)`;
      OscEngine.atualizar({ ...estado });
      atualizarFormula();
    }

    aplicar(estado[param]); // estado inicial

    // ── Drag ─────────────────────────────────────────────
    // Pixels que o usuário precisa arrastar para mudar 1 unidade
    const SENS = 22;
    let isDragging = false;
    let startY     = 0;
    let startVal   = 0;

    function iniciarDrag(clientY) {
      isDragging = true;
      startY     = clientY;
      startVal   = estado[param];
      knobEl.classList.add('dragging');
      // Cursor global durante o drag
      document.body.style.cursor = 'ns-resize';
    }

    function moverDrag(clientY) {
      if (!isDragging) return;
      const delta = (startY - clientY) / SENS;
      aplicar(startVal + delta);
    }

    function terminarDrag() {
      if (!isDragging) return;
      isDragging = false;
      knobEl.classList.remove('dragging');
      document.body.style.cursor = '';
      verificarVitoria();
    }

    // Mouse events
    knobEl.addEventListener('mousedown', e => {
      e.preventDefault();
      iniciarDrag(e.clientY);
    });

    // Touch events
    knobEl.addEventListener('touchstart', e => {
      e.preventDefault();
      iniciarDrag(e.touches[0].clientY);
    }, { passive: false });

    // Scroll/wheel no knob
    knobEl.addEventListener('wheel', e => {
      e.preventDefault();
      aplicar(estado[param] + (e.deltaY < 0 ? 1 : -1));
      verificarVitoria();
    }, { passive: false });

    return { aplicar };
  }

  // Eventos globais de move/up (captura mesmo fora do knob)
  window.addEventListener('mousemove', e => {
    Object.keys(PARAMS).forEach(p => knobs[p] && knobs[p]._mover(e.clientY));
  });
  window.addEventListener('mouseup', () => {
    Object.keys(PARAMS).forEach(p => knobs[p] && knobs[p]._terminar());
  });
  window.addEventListener('touchmove', e => {
    Object.keys(PARAMS).forEach(p => knobs[p] && knobs[p]._mover(e.touches[0].clientY));
  }, { passive: true });
  window.addEventListener('touchend', () => {
    Object.keys(PARAMS).forEach(p => knobs[p] && knobs[p]._terminar());
  });

  // ── Recria com referências aos handlers globais ───────────
  const knobs = {};
  ['A', 'B', 'C', 'D'].forEach(param => {
    const cfg     = PARAMS[param];
    const grupo   = document.getElementById(`knob-group-${param}`);
    if (!grupo) return;
    const knobEl  = grupo.querySelector('.knob');
    const valEl   = grupo.querySelector('.knob-value');

    const SENS = 22;
    let isDragging = false, startY = 0, startVal = 0;

    function aplicar(v) {
      v = Math.max(cfg.min, Math.min(cfg.max, Math.round(v)));
      estado[param] = v;
      valEl.textContent = v >= 0 ? '+' + v : String(v);
      knobEl.style.transform = `rotate(${-135 + ((v - cfg.min) / (cfg.max - cfg.min)) * 270}deg)`;
      OscEngine.atualizar({ ...estado });
      atualizarFormula();
      // Som de tick apenas quando o valor inteiro muda
      if (audioIniciado && v !== estadoAnterior) OscAudio.knobTick(v);
      estadoAnterior = v;
    }

    let estadoAnterior = estado[param];
    aplicar(estado[param]);

    knobEl.addEventListener('mousedown', e => {
      e.preventDefault();
      isDragging = true; startY = e.clientY; startVal = estado[param];
      knobEl.classList.add('dragging');
      document.body.style.cursor = 'ns-resize';
    });

    knobEl.addEventListener('touchstart', e => {
      e.preventDefault();
      isDragging = true; startY = e.touches[0].clientY; startVal = estado[param];
      knobEl.classList.add('dragging');
    }, { passive: false });

    knobEl.addEventListener('wheel', e => {
      e.preventDefault();
      aplicar(estado[param] + (e.deltaY < 0 ? 1 : -1));
      verificarVitoria();
    }, { passive: false });

    knobs[param] = {
      _mover(clientY) {
        if (!isDragging) return;
        aplicar(startVal + (startY - clientY) / SENS);
      },
      _terminar() {
        if (!isDragging) return;
        isDragging = false;
        knobEl.classList.remove('dragging');
        document.body.style.cursor = '';
        verificarVitoria();
      }
    };
  });

  // ── Toggle SEN / COS ────────────────────────────────────
  const funcBtns = document.querySelectorAll('.func-btn');
  funcBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      funcBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      estado.tipoFunc = btn.dataset.func;
      OscEngine.atualizar({ ...estado });
      atualizarFormula();
      OscAudio.trocarFuncao();
      verificarVitoria();
    });
  });

  // ── Fórmula ao vivo ──────────────────────────────────────
  function atualizarFormula() {
    const el = document.getElementById('formula-live');
    if (!el) return;
    const func = estado.tipoFunc === 'sen' ? 'sen' : 'cos';
    const A = estado.A >= 0 ? `+${estado.A}` : String(estado.A);
    el.innerHTML =
      `f(x) = <span>${A}</span> + <span>${estado.B}</span>&middot;${func}(<span>${estado.C}</span>&middot;&pi;x + <span>${estado.D}</span>)`;
  }
  atualizarFormula();

  // ── Verificação de vitória via AJAX ─────────────────────
  let jaVenceu = false;

  async function verificarVitoria() {
    if (jaVenceu) return;
    try {
      const resp = await fetch(VERIFICAR_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
          A: estado.A, B: estado.B, C: estado.C, D: estado.D,
          tipo_func: estado.tipoFunc
        })
      });
      const data = await resp.json();
      if (data.correto) {
        jaVenceu = true;
        OscEngine.setVitoria(true);
        OscAudio.vitoria();
        setTimeout(() => {
          document.getElementById('victory-overlay').classList.add('show');
        }, 700);
      }
    } catch (e) {
      console.warn('Verificação AJAX falhou:', e);
    }
  }

  // ── CSRF ─────────────────────────────────────────────────
  function getCookie(name) {
    const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return m ? m.pop() : '';
  }

  // ── Fechar overlay de vitória ────────────────────────────
  document.getElementById('btn-proximo')?.addEventListener('click', () => {
    document.getElementById('victory-overlay').classList.remove('show');
  });

  // ── Botão de confirmação manual (mobile) ─────────────────
  document.getElementById('btn-confirmar')?.addEventListener('click', () => {
    OscAudio.trocarFuncao(); // feedback sonoro de "enviando"
    verificarVitoria();
  });
});