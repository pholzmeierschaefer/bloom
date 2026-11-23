# -*- coding: utf-8 -*-
"""
Biblioteca mínima para gerar os PDFs do trabalho usando apenas pycairo.
Contém: escritor de texto com quebra de linha (negrito **x** e monoespaçado `x`),
documento A4 com fluxo de páginas (parágrafos, listas, tabelas, código) e gráficos simples.
"""
import math
import re
import cairo

SANS = "DejaVu Sans"
MONO = "DejaVu Sans Mono"

PRETO = (0.1, 0.1, 0.1)
CINZA = (0.45, 0.45, 0.45)
CINZA_CLARO = (0.93, 0.93, 0.93)
AZUL = (0.12, 0.35, 0.65)
VERMELHO = (0.78, 0.15, 0.15)
VERDE = (0.15, 0.55, 0.25)
LARANJA = (0.9, 0.5, 0.1)
ROXO = (0.45, 0.25, 0.65)


def definir_fonte(ctx, tam, negrito=False, mono=False):
    """Seleciona a fonte no contexto cairo."""
    peso = cairo.FONT_WEIGHT_BOLD if negrito else cairo.FONT_WEIGHT_NORMAL
    ctx.select_font_face(MONO if mono else SANS, cairo.FONT_SLANT_NORMAL, peso)
    ctx.set_font_size(tam)


def _atomos(texto, negrito_base=False, mono_base=False):
    """Quebra o texto em 'átomos' (palavra, negrito, mono, espaço_antes)."""
    atomos = []
    espaco = False
    for pedaco in re.split(r"(\*\*.+?\*\*|`.+?`)", texto):
        if not pedaco:
            continue
        neg, mon = negrito_base, mono_base
        if pedaco.startswith("**") and pedaco.endswith("**") and len(pedaco) > 4:
            pedaco, neg = pedaco[2:-2], True
        elif pedaco.startswith("`") and pedaco.endswith("`") and len(pedaco) > 2:
            pedaco, mon = pedaco[1:-1], True
        for parte in re.findall(r"\s+|\S+", pedaco):
            if parte.isspace():
                espaco = True
            else:
                atomos.append((parte, neg, mon, espaco))
                espaco = False
    return atomos


class Escritor:
    """Escreve texto com quebra automática de linha dentro de uma largura."""

    def __init__(self, ctx):
        self.ctx = ctx

    def _largura(self, texto, tam, neg, mon):
        definir_fonte(self.ctx, tam, neg, mon)
        return self.ctx.text_extents(texto).x_advance

    def linhas(self, texto, largura, tam, negrito=False, mono=False):
        """Retorna lista de linhas; cada linha é lista de (texto, neg, mon, x_relativo)."""
        resultado = []
        for paragrafo in texto.split("\n"):
            linha, x = [], 0.0
            for palavra, neg, mon, esp in _atomos(paragrafo, negrito, mono):
                larg = self._largura(palavra, tam, neg, mon)
                esp_larg = self._largura(" ", tam, False, mon) if (esp and linha) else 0
                if linha and x + esp_larg + larg > largura:
                    resultado.append(linha)
                    linha, x, esp_larg = [], 0.0, 0
                linha.append((palavra, neg, mon, x + esp_larg))
                x += esp_larg + larg
            resultado.append(linha)
        return resultado

    def altura(self, texto, largura, tam, entrelinha=1.3, negrito=False, mono=False):
        return len(self.linhas(texto, largura, tam, negrito, mono)) * tam * entrelinha

    def desenhar(self, texto, x, y, largura, tam, cor=PRETO, entrelinha=1.3,
                 negrito=False, mono=False, alinhar="esq"):
        """Desenha o texto com topo em y. Retorna a altura usada."""
        ctx = self.ctx
        linhas = self.linhas(texto, largura, tam, negrito, mono)
        ctx.set_source_rgb(*cor)
        for i, linha in enumerate(linhas):
            base = y + tam * 1.0 + i * tam * entrelinha
            deslocamento = 0
            if linha and alinhar != "esq":
                u = linha[-1]
                fim = u[3] + self._largura(u[0], tam, u[1], u[2])
                deslocamento = (largura - fim) / (2 if alinhar == "centro" else 1)
            for palavra, neg, mon, rel in linha:
                definir_fonte(ctx, tam, neg, mon)
                ctx.set_source_rgb(*cor)
                ctx.move_to(x + deslocamento + rel, base)
                ctx.show_text(palavra)
        return len(linhas) * tam * entrelinha


class Documento:
    """Documento A4 com fluxo vertical e quebra de página automática."""

    def __init__(self, caminho, titulo_cabecalho, margem=52, largura=595.28, altura=841.89):
        self.superficie = cairo.PDFSurface(caminho, largura, altura)
        self.superficie.set_metadata(cairo.PDF_METADATA_TITLE, titulo_cabecalho)
        self.ctx = cairo.Context(self.superficie)
        self.esc = Escritor(self.ctx)
        self.L, self.A, self.m = largura, altura, margem
        self.cab = titulo_cabecalho
        self.pagina = 0
        self.y = 0
        self.nova_pagina(primeira=True)

    # ----- páginas -----
    def nova_pagina(self, primeira=False):
        if not primeira:
            self.ctx.show_page()
        self.pagina += 1
        ctx = self.ctx
        definir_fonte(ctx, 7.5)
        ctx.set_source_rgb(*CINZA)
        ctx.move_to(self.m, 30)
        ctx.show_text(self.cab)
        rotulo = "Página %d" % self.pagina
        ctx.move_to(self.L - self.m - ctx.text_extents(rotulo).x_advance, self.A - 26)
        ctx.show_text(rotulo)
        ctx.set_line_width(0.4)
        ctx.move_to(self.m, 35)
        ctx.line_to(self.L - self.m, 35)
        ctx.stroke()
        self.y = self.m - 4 + 6

    def garantir(self, h):
        if self.y + h > self.A - self.m + 6:
            self.nova_pagina()

    @property
    def largura_util(self):
        return self.L - 2 * self.m

    # ----- blocos -----
    def titulo(self, texto, subtitulo=None):
        self.ctx.set_source_rgb(*AZUL)
        self.y += self.esc.desenhar(texto, self.m, self.y, self.largura_util, 17, AZUL, 1.2, negrito=True)
        if subtitulo:
            self.y += self.esc.desenhar(subtitulo, self.m, self.y + 1, self.largura_util, 8.8, CINZA, 1.3)
        self.y += 5

    def secao(self, texto, tam=11):
        self.garantir(tam * 3)
        self.y += 4
        self.y += self.esc.desenhar(texto, self.m, self.y, self.largura_util, tam, AZUL, 1.2, negrito=True)
        self.ctx.set_source_rgb(*AZUL)
        self.ctx.set_line_width(0.6)
        self.ctx.move_to(self.m, self.y + 0.5)
        self.ctx.line_to(self.L - self.m, self.y + 0.5)
        self.ctx.stroke()
        self.y += 4

    def subsecao(self, texto, tam=9.5):
        self.garantir(tam * 3)
        self.y += 2
        self.y += self.esc.desenhar(texto, self.m, self.y, self.largura_util, tam, PRETO, 1.25, negrito=True)
        self.y += 1.5

    def paragrafo(self, texto, tam=9.2, depois=3.5, cor=PRETO, entrelinha=1.28):
        linhas_h = tam * entrelinha
        n = len(self.esc.linhas(texto, self.largura_util, tam))
        if n <= 3:
            self.garantir(n * linhas_h)
        else:
            self.garantir(2 * linhas_h)
        self.y += self.esc.desenhar(texto, self.m, self.y, self.largura_util, tam, cor, entrelinha) + depois

    def lista(self, itens, tam=9.2, marcador="•", recuo=11, depois=1.6, entrelinha=1.26):
        for item in itens:
            n = len(self.esc.linhas(item, self.largura_util - recuo, tam))
            self.garantir(min(n, 2) * tam * entrelinha)
            self.ctx.set_source_rgb(*PRETO)
            definir_fonte(self.ctx, tam)
            self.ctx.move_to(self.m + 2, self.y + tam)
            self.ctx.show_text(marcador)
            self.y += self.esc.desenhar(item, self.m + recuo, self.y, self.largura_util - recuo, tam, PRETO, entrelinha) + depois
        self.y += 1.5

    def espaco(self, h):
        self.y += h

    def codigo(self, texto, tam=7.2, cor_fundo=CINZA_CLARO):
        """Bloco monoespaçado (sem quebra automática; linhas já devem caber)."""
        ctx = self.ctx
        linhas = texto.rstrip("\n").split("\n")
        passo = tam * 1.25
        i = 0
        while i < len(linhas):
            livre = int((self.A - self.m + 6 - self.y - 6) / passo)
            if livre < 3:
                self.nova_pagina()
                continue
            bloco = linhas[i:i + livre]
            h = len(bloco) * passo + 6
            ctx.set_source_rgb(*cor_fundo)
            ctx.rectangle(self.m, self.y, self.largura_util, h)
            ctx.fill()
            for k, linha in enumerate(bloco):
                definir_fonte(ctx, tam, mono=True)
                ctx.set_source_rgb(*PRETO)
                ctx.move_to(self.m + 4, self.y + 3 + tam + k * passo)
                ctx.show_text(linha)
            self.y += h
            i += len(bloco)
        self.y += 4

    def tabela(self, cabecalho, linhas, larguras, tam=8, alinhar=None, zebra=True, destaque_cab=AZUL):
        """larguras: proporções relativas. alinhar: lista de 'esq'/'centro'/'dir' por coluna."""
        ctx = self.ctx
        total = float(sum(larguras))
        cols = [self.largura_util * l / total for l in larguras]
        alinhar = alinhar or ["esq"] * len(cols)
        pad = 3.0

        def altura_linha(celulas, negrito=False):
            return max(self.esc.altura(str(c), cols[j] - 2 * pad, tam, 1.2, negrito) for j, c in enumerate(celulas)) + 2 * pad - 1

        def desenhar_linha(celulas, fundo=None, negrito=False, cor=PRETO):
            h = altura_linha(celulas, negrito)
            self.garantir(h + 1)
            if fundo:
                ctx.set_source_rgb(*fundo)
                ctx.rectangle(self.m, self.y, self.largura_util, h)
                ctx.fill()
            x = self.m
            for j, c in enumerate(celulas):
                self.esc.desenhar(str(c), x + pad, self.y + pad - 0.5, cols[j] - 2 * pad, tam, cor, 1.2, negrito, alinhar=alinhar[j])
                x += cols[j]
            ctx.set_source_rgb(0.75, 0.75, 0.75)
            ctx.set_line_width(0.3)
            ctx.move_to(self.m, self.y + h)
            ctx.line_to(self.m + self.largura_util, self.y + h)
            ctx.stroke()
            self.y += h

        total_h = altura_linha(cabecalho, True) + sum(altura_linha(l) for l in linhas)
        if total_h < (self.A - 2 * self.m) * 0.6:
            self.garantir(total_h + 2)  # tabela pequena: não separar entre páginas
        desenhar_linha(cabecalho, destaque_cab, True, (1, 1, 1))
        for i, linha in enumerate(linhas):
            fundo = (0.96, 0.96, 0.98) if (zebra and i % 2) else None
            if self.y + altura_linha(linha) > self.A - self.m + 6:
                self.nova_pagina()
                desenhar_linha(cabecalho, destaque_cab, True, (1, 1, 1))
            desenhar_linha(linha, fundo)
        self.y += 5

    def figura(self, altura, desenhar):
        """desenhar(ctx, x, y, largura, altura) desenha livremente na área reservada."""
        self.garantir(altura)
        desenhar(self.ctx, self.m, self.y, self.largura_util, altura)
        self.y += altura + 4

    def legenda(self, texto, tam=7.8):
        self.y += self.esc.desenhar(texto, self.m, self.y, self.largura_util, tam, CINZA, 1.25, alinhar="centro") + 4

    def fim(self):
        self.ctx.show_page()
        self.superficie.finish()


# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------
def _transformar(v, log):
    return math.log10(v) if log else v


def grafico(ctx, x, y, w, h, series, xlabel, ylabel, xlim, ylim, xticks, yticks,
            xlog=False, ylog=False, xfmt=str, yfmt=str, titulo=None, tam=7.5, linha_ref=None, legenda_abaixo=True):
    """
    Gráfico de linhas/pontos. series: lista de dicts {label, cor, pontos, linha(bool), marcador(bool), tracejado(bool)}.
    linha_ref: lista de pontos de uma linha de referência (cinza tracejada).
    """
    esc = Escritor(ctx)
    esq, dir_, topo, base = 46, 10, 16 if titulo else 6, 30 + (12 if legenda_abaixo else 0)
    px, py, pw, ph = x + esq, y + topo, w - esq - dir_, h - topo - base

    def X(v):
        a, b = _transformar(xlim[0], xlog), _transformar(xlim[1], xlog)
        return px + (_transformar(v, xlog) - a) / (b - a) * pw

    def Y(v):
        a, b = _transformar(ylim[0], ylog), _transformar(ylim[1], ylog)
        return py + ph - (_transformar(v, ylog) - a) / (b - a) * ph

    if titulo:
        esc.desenhar(titulo, x, y, w, tam + 1, PRETO, 1.2, negrito=True, alinhar="centro")
    ctx.set_line_width(0.3)
    for v in yticks:
        ctx.set_source_rgb(0.85, 0.85, 0.85)
        ctx.move_to(px, Y(v)); ctx.line_to(px + pw, Y(v)); ctx.stroke()
        definir_fonte(ctx, tam); ctx.set_source_rgb(*CINZA)
        s = yfmt(v); ctx.move_to(px - 4 - ctx.text_extents(s).x_advance, Y(v) + tam * 0.35); ctx.show_text(s)
    for v in xticks:
        ctx.set_source_rgb(0.85, 0.85, 0.85)
        ctx.move_to(X(v), py); ctx.line_to(X(v), py + ph); ctx.stroke()
        definir_fonte(ctx, tam); ctx.set_source_rgb(*CINZA)
        s = xfmt(v); ctx.move_to(X(v) - ctx.text_extents(s).x_advance / 2, py + ph + tam + 3); ctx.show_text(s)
    ctx.set_source_rgb(*PRETO); ctx.set_line_width(0.8)
    ctx.rectangle(px, py, pw, ph); ctx.stroke()
    # rótulos dos eixos
    esc.desenhar(xlabel, px, py + ph + tam + 8, pw, tam, PRETO, 1.2, alinhar="centro")
    ctx.save()
    ctx.translate(x + 2, py + ph / 2 + 20)
    ctx.rotate(-math.pi / 2)
    definir_fonte(ctx, tam); ctx.set_source_rgb(*PRETO)
    ctx.move_to(0, 7); ctx.show_text(ylabel)
    ctx.restore()
    # linha de referência
    if linha_ref:
        ctx.set_source_rgb(0.5, 0.5, 0.5); ctx.set_line_width(0.8); ctx.set_dash([3, 2])
        for i, (a, b) in enumerate(linha_ref):
            (ctx.move_to if i == 0 else ctx.line_to)(X(a), Y(b))
        ctx.stroke(); ctx.set_dash([])
    # séries
    for s in series:
        ctx.set_source_rgb(*s["cor"]); ctx.set_line_width(1.2)
        if s.get("tracejado"):
            ctx.set_dash([3, 2])
        if s.get("linha", True):
            for i, (a, b) in enumerate(s["pontos"]):
                (ctx.move_to if i == 0 else ctx.line_to)(X(a), Y(b))
            ctx.stroke()
        ctx.set_dash([])
        if s.get("marcador", True):
            for a, b in s["pontos"]:
                ctx.arc(X(a), Y(b), 2.2, 0, 2 * math.pi); ctx.fill()
    # legenda
    lx = px
    ly = y + h - tam - 1
    for s in series:
        ctx.set_source_rgb(*s["cor"]); ctx.set_line_width(1.5)
        ctx.move_to(lx, ly + tam * 0.4); ctx.line_to(lx + 12, ly + tam * 0.4); ctx.stroke()
        definir_fonte(ctx, tam)
        ctx.set_source_rgb(*PRETO); ctx.move_to(lx + 15, ly + tam * 0.8); ctx.show_text(s["label"])
        lx += 15 + ctx.text_extents(s["label"]).x_advance + 12
    if linha_ref:
        ctx.set_source_rgb(0.5, 0.5, 0.5); ctx.set_dash([3, 2]); ctx.move_to(lx, ly + tam * 0.4); ctx.line_to(lx + 12, ly + tam * 0.4); ctx.stroke(); ctx.set_dash([])
        definir_fonte(ctx, tam); ctx.set_source_rgb(*PRETO); ctx.move_to(lx + 15, ly + tam * 0.8); ctx.show_text("ideal (y = x)")


def desenhar_bits(ctx, x, y, bits, celula=16, destaque=None, rotulos=True, tam=9, cor_um=(0.85, 0.9, 1.0)):
    """Desenha um vetor de bits (string '0101...'). destaque: {posicao: cor RGB} para realçar células."""
    destaque = destaque or {}
    for i, b in enumerate(bits):
        cx = x + i * celula
        if i in destaque:
            ctx.set_source_rgb(*destaque[i])
        elif b == "1":
            ctx.set_source_rgb(*cor_um)
        else:
            ctx.set_source_rgb(1, 1, 1)
        ctx.rectangle(cx, y, celula, celula)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.3, 0.3, 0.3)
        ctx.set_line_width(0.7)
        ctx.stroke()
        definir_fonte(ctx, tam, negrito=(b == "1"), mono=True)
        ctx.set_source_rgb(*PRETO)
        ctx.move_to(cx + celula / 2 - ctx.text_extents(b).x_advance / 2, y + celula / 2 + tam * 0.35)
        ctx.show_text(b)
        if rotulos:
            definir_fonte(ctx, tam * 0.65)
            ctx.set_source_rgb(*CINZA)
            s = str(i)
            ctx.move_to(cx + celula / 2 - ctx.text_extents(s).x_advance / 2, y + celula + tam * 0.85)
            ctx.show_text(s)


def caixa(ctx, x, y, w, h, texto, tam=11, fundo=(0.9, 0.94, 1.0), borda=AZUL, cor=PRETO, negrito=False):
    """Caixa com texto centralizado."""
    ctx.set_source_rgb(*fundo)
    ctx.rectangle(x, y, w, h)
    ctx.fill_preserve()
    ctx.set_source_rgb(*borda)
    ctx.set_line_width(1.2)
    ctx.stroke()
    esc = Escritor(ctx)
    alt = esc.altura(texto, w - 10, tam, 1.2, negrito)
    esc.desenhar(texto, x + 5, y + (h - alt) / 2, w - 10, tam, cor, 1.2, negrito, alinhar="centro")


def seta(ctx, x1, y1, x2, y2, cor=(0.3, 0.3, 0.3), larg=1.5):
    """Seta simples de (x1,y1) até (x2,y2)."""
    ctx.set_source_rgb(*cor)
    ctx.set_line_width(larg)
    ctx.move_to(x1, y1)
    ctx.line_to(x2, y2)
    ctx.stroke()
    ang = math.atan2(y2 - y1, x2 - x1)
    ctx.move_to(x2, y2)
    ctx.line_to(x2 - 7 * math.cos(ang - 0.45), y2 - 7 * math.sin(ang - 0.45))
    ctx.line_to(x2 - 7 * math.cos(ang + 0.45), y2 - 7 * math.sin(ang + 0.45))
    ctx.close_path()
    ctx.fill()
