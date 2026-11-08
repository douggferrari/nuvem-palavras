// Nuvem ao vivo: consulta /api/nuvem a cada poucos segundos e, quando algo
// muda, refaz o layout. Cada palavra parte do centro e anda numa espiral até
// achar espaço livre; as mais frequentes são maiores e entram primeiro.
(() => {
  "use strict";

  const INTERVALO_MS = 3000;
  const CORES = 7;
  const ANEL = 8;            // px que a espiral abre a cada volta
  const PASSO = 4;           // px de arco entre dois pontos testados
  const ALTURA_LINHA = 1.15; // igual ao line-height de .palavra

  const area = document.getElementById("nuvem");
  const vazio = document.getElementById("vazio");
  const elPergunta = document.getElementById("pergunta");
  const elTotal = document.getElementById("total");
  const qr = document.getElementById("qr");
  const medidor = document.createElement("canvas").getContext("2d");
  const palavras = new Map(); // chave -> <span> na tela
  let dados = null;
  let recebido = "";

  const tema = new URLSearchParams(location.search).get("tema");
  if (tema === "escuro") document.documentElement.dataset.theme = "dark";
  if (tema === "claro") document.documentElement.dataset.theme = "light";

  function hash(texto) {
    let h = 7;
    for (let i = 0; i < texto.length; i++) h = (h * 31 + texto.charCodeAt(i)) >>> 0;
    return h;
  }

  // Índice da caixa ocupada que colide, ou -1. Testa primeiro a última que
  // bateu: o ponto seguinte da espiral quase sempre bate na mesma.
  function colisao(x, y, w, h, ocupados, ultima) {
    const u = ocupados[ultima];
    if (u && x < u.x + u.w && u.x < x + w && y < u.y + u.h && u.y < y + h) return ultima;
    for (let i = 0; i < ocupados.length; i++) {
      const o = ocupados[i];
      if (x < o.x + o.w && o.x < x + w && y < o.y + o.h && o.y < y + h) return i;
    }
    return -1;
  }

  // O QR fica por cima da área da nuvem: entra como obstáculo para nenhuma
  // palavra cair embaixo dele (ampliado, ele cobre de propósito).
  function obstaculos() {
    if (qr.classList.contains("ampliado") || getComputedStyle(qr).display === "none") return [];
    const a = area.getBoundingClientRect();
    const q = qr.getBoundingClientRect();
    const m = 12;
    return [{ x: q.left - a.left - m, y: q.top - a.top - m, w: q.width + 2 * m, h: q.height + 2 * m }];
  }

  // Posição de cada caixa (null = não coube). Com exigirTodas, desiste na
  // primeira que não couber e devolve null: a escala vai diminuir mesmo.
  function posicionar(caixas, larg, alt, exigirTodas) {
    const cx = larg / 2;
    const cy = alt / 2;
    const achatar = Math.min(Math.max(larg / alt, 1), 2.5); // espiral elíptica ocupa a tela larga
    const raioMax = Math.hypot(cx / achatar, cy);
    const ocupados = obstaculos();
    const posicoes = [];
    for (const c of caixas) {
      let achada = null;
      let ultima = -1;
      const cabe = c.w <= larg && c.h <= alt;
      for (let ang = c.angulo, raio = 0; cabe && raio <= raioMax; ) {
        const x = cx + raio * Math.cos(ang) * achatar - c.w / 2;
        const y = cy + raio * Math.sin(ang) - c.h / 2;
        if (x >= 0 && y >= 0 && x + c.w <= larg && y + c.h <= alt) {
          ultima = colisao(x, y, c.w, c.h, ocupados, ultima);
          if (ultima < 0) {
            achada = { x, y, w: c.w, h: c.h };
            break;
          }
        }
        ang += PASSO / Math.max(raio, PASSO);
        raio = (ANEL * (ang - c.angulo)) / (2 * Math.PI);
      }
      if (!achada && exigirTodas) return null;
      if (achada) ocupados.push(achada);
      posicoes.push(achada);
    }
    return posicoes;
  }

  function medir(termos, tamanhos, familia) {
    return termos.map((t, i) => {
      const tam = tamanhos[i];
      const folga = Math.max(3, tam * 0.16);
      medidor.font = `700 ${tam}px ${familia}`;
      return {
        tam,
        folga,
        w: Math.ceil(medidor.measureText(t.texto).width + 2 * folga),
        h: Math.ceil(tam * ALTURA_LINHA + folga * 0.5),
        angulo: (hash(t.chave) % 628) / 100,
      };
    });
  }

  // Maior escala em que todas as palavras cabem; no limite, mostra as que couberem.
  function montar(termos) {
    const larg = area.clientWidth;
    const alt = area.clientHeight;
    if (!larg || !alt) return { caixas: [], pos: [] };
    const familia = getComputedStyle(area).fontFamily;
    const maior = Math.min(alt * 0.26, larg * 0.16);
    const menor = Math.max(16, maior * 0.2);
    const nMax = termos[0].n;
    const nMin = termos[termos.length - 1].n;
    const base = termos.map((t) =>
      nMax === nMin ? maior : menor + (maior - menor) * Math.sqrt((t.n - nMin) / (nMax - nMin)));
    const escalar = (e) => base.map((b) => Math.max(10, Math.round(b * e * 2) / 2));

    // Chute inicial: caixas somando ~45% da área e a mais larga cabendo na largura.
    let caixas = medir(termos, escalar(1), familia);
    const ocupacao = caixas.reduce((s, c) => s + c.w * c.h, 0) / (larg * alt);
    const largMax = Math.max(...caixas.map((c) => c.w));
    let escala = Math.min(1, Math.sqrt(0.45 / ocupacao), (0.95 * larg) / largMax);
    for (let i = 0; i < 30; i++) {
      caixas = medir(termos, escalar(escala), familia);
      const pos = posicionar(caixas, larg, alt, true);
      if (pos) return { caixas, pos };
      escala *= 0.92;
    }
    return { caixas, pos: posicionar(caixas, larg, alt, false) };
  }

  function desenhar(termos) {
    vazio.hidden = termos.length > 0;
    const { caixas, pos } = termos.length ? montar(termos) : { caixas: [], pos: [] };
    const presentes = new Set();
    termos.forEach((t, i) => {
      const r = pos[i];
      if (!r) return;
      const c = caixas[i];
      let el = palavras.get(t.chave);
      const nova = !el;
      if (nova) {
        el = document.createElement("span");
        el.className = "palavra nova c" + (hash(t.chave) % CORES);
        el.addEventListener("animationend", () => el.classList.remove("nova"), { once: true });
        palavras.set(t.chave, el);
      }
      el.textContent = t.texto;
      el.title = t.n === 1 ? "1 resposta" : `${t.n} respostas`;
      el.style.fontSize = `${c.tam}px`;
      el.style.left = `${r.x + c.folga}px`;
      el.style.top = `${r.y + c.folga * 0.25}px`;
      if (nova) area.appendChild(el);
      presentes.add(t.chave);
    });
    for (const [chave, el] of palavras) {
      if (!presentes.has(chave)) {
        el.remove();
        palavras.delete(chave);
      }
    }
  }

  function aplicar(d) {
    elPergunta.textContent = d.pergunta;
    elTotal.textContent = d.total === 1 ? "1 resposta" : `${d.total} respostas`;
    desenhar(d.termos);
  }

  async function atualizar() {
    try {
      const resp = await fetch("/api/nuvem", { cache: "no-store" });
      if (resp.ok) {
        const texto = await resp.text();
        if (texto !== recebido) {
          recebido = texto;
          dados = JSON.parse(texto);
          aplicar(dados);
        }
      }
    } catch {
      // rede caiu: tenta de novo no próximo ciclo
    }
    setTimeout(atualizar, INTERVALO_MS);
  }

  let espera;
  addEventListener("resize", () => {
    clearTimeout(espera);
    espera = setTimeout(() => dados && desenhar(dados.termos), 200);
  });
  qr.addEventListener("click", () => {
    qr.classList.toggle("ampliado");
    if (dados) desenhar(dados.termos);
  });

  atualizar();
})();
