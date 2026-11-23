# -*- coding: utf-8 -*-
"""Roteiro dos slides do seminário: cada página 16:9 é um slide (conteúdo) + notas de fala."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gerar_pdfs import *  # noqa: E402,F401,F403

LARG, ALT = 960.0, 540.0
M = 36
TOTAL = 16
BLOCOS = {"capa": "Abertura", "problema": "Problema e motivação", "solucao": "Solução", "critica": "Análise crítica",
          "aplic": "Aplicações", "sintese": "Síntese"}
COR_BLOCO = {"capa": CINZA, "problema": VERMELHO, "solucao": AZUL, "critica": ROXO, "aplic": VERDE, "sintese": LARANJA}


class Apresentacao:
    def __init__(self, caminho):
        self.sup = cairo.PDFSurface(caminho, LARG, ALT)
        self.sup.set_metadata(cairo.PDF_METADATA_TITLE, "Roteiro dos slides · Filtro de Bloom")
        self.ctx = cairo.Context(self.sup)
        self.esc = Escritor(self.ctx)
        self.n = 0

    def slide(self, bloco, tempo, titulo, corpo, notas):
        ctx, esc = self.ctx, self.esc
        self.n += 1
        cor = COR_BLOCO[bloco]
        # faixa superior com identificação (não faz parte do slide final)
        ctx.set_source_rgb(*cor)
        ctx.rectangle(0, 0, LARG, 6)
        ctx.fill()
        esc.desenhar("SLIDE %d de %d  ·  %s  ·  tempo sugerido: %s" % (self.n, TOTAL, BLOCOS[bloco], tempo), M, 12, LARG - 2 * M, 9, cor, 1.2, negrito=True)
        esc.desenhar(titulo, M, 30, LARG - 2 * M, 27, AZUL, 1.15, negrito=True)
        # área do slide
        corpo(ctx, esc, M, 86, LARG - 2 * M, 300)
        # notas de fala
        ctx.set_source_rgb(0.95, 0.95, 0.95)
        ctx.rectangle(0, 404, LARG, ALT - 404)
        ctx.fill()
        esc.desenhar("NOTAS DE FALA (não vão no slide)", M, 410, 300, 8, CINZA, 1.2, negrito=True)
        esc.desenhar(notas, M, 424, LARG - 2 * M, 10.2, PRETO, 1.3)
        ctx.show_page()

    def fim(self):
        self.sup.finish()


def pontos(ctx, esc, itens, x, y, w, tam=16, depois=7, marcador="•"):
    """Lista de tópicos do slide; retorna o y final."""
    for item in itens:
        definir_fonte(ctx, tam)
        ctx.set_source_rgb(*AZUL)
        ctx.move_to(x, y + tam)
        ctx.show_text(marcador)
        y += esc.desenhar(item, x + 16, y, w - 16, tam, PRETO, 1.25) + depois
    return y


def rotulo(ctx, esc, texto, x, y, w, tam=11, cor=CINZA, negrito=False, alinhar="esq"):
    return esc.desenhar(texto, x, y, w, tam, cor, 1.2, negrito, alinhar=alinhar)


ESTADOS = ["000000000000000000000000", "000010000100001000000000", "001010000101001000001000", "001010010101011000001010"]
NOVOS = [None, {4, 9, 14}, {2, 11, 20}, {7, 13, 22}]
LARANJA_CLARO = (1.0, 0.8, 0.5)
VERDE_CLARO = (0.7, 0.9, 0.7)
VERMELHO_CLARO = (1.0, 0.7, 0.7)


def gerar():
    ap = Apresentacao(os.path.join(DOCS, "slides.pdf"))

    # ---------------------------------------------------------------- 1
    def s1(ctx, esc, x, y, w, h):
        esc.desenhar("Filtro de Bloom", x, y + 8, w, 44, AZUL, 1.1, True, alinhar="centro")
        esc.desenhar("Space/Time Trade-offs in Hash Coding with Allowable Errors", x, y + 66, w, 20, PRETO, 1.2, alinhar="centro")
        esc.desenhar("Burton H. Bloom · Communications of the ACM, 13(7), 422–426 · 1970", x, y + 96, w, 14, CINZA, 1.2, alinhar="centro")
        esc.desenhar("Estruturas de Dados II (GEX1210) · UFFS Campus Chapecó", x, y + 150, w, 15, PRETO, 1.2, alinhar="centro")
        esc.desenhar(" · ".join(INTEGRANTES), x, y + 185, w, 13, CINZA, 1.3, alinhar="centro")
    ap.slide("capa", "0:30", "Capa", s1,
             "Abrir com a pergunta: “como saber se algo está em um conjunto enorme sem guardar o conjunto inteiro?”. Apresentar o artigo (autor, ano, revista) e os integrantes. "
             "Dizer que o roteiro é: problema → solução com exemplo → análise crítica → aplicações → síntese.")

    # ---------------------------------------------------------------- 2
    def s2(ctx, esc, x, y, w, h):
        pontos(ctx, esc, [
            "Tarefa: testar mensagens, **uma a uma**, para saber se pertencem a um conjunto.",
            "Caso do artigo: hifenizar 500.000 palavras.",
            "90% seguem regras simples; **10% (50.000) são exceções** que só o dicionário sabe.",
            "O dicionário é grande demais para a memória principal → fica **em disco** (lento).",
            "Quase todas as consultas são de palavras que **não** estão nas exceções.",
        ], x, y, 430, 16, 9)
        bx = x + 590
        caixa(ctx, bx, y + 10, 140, 44, "palavra", 14, (0.95, 0.95, 0.95), CINZA)
        seta(ctx, bx + 70, y + 54, bx + 70, y + 84)
        caixa(ctx, bx - 20, y + 84, 180, 52, "tem exceção?\n(consultar o dicionário)", 12, (1, 0.92, 0.85), LARANJA)
        seta(ctx, bx + 30, y + 136, bx - 40, y + 176)
        seta(ctx, bx + 110, y + 136, bx + 200, y + 176)
        caixa(ctx, bx - 120, y + 176, 170, 60, "regras simples\n(90% dos casos)", 12, (0.88, 0.97, 0.88), VERDE)
        caixa(ctx, bx + 120, y + 176, 170, 60, "dicionário em DISCO\n(10% dos casos)", 12, (1, 0.88, 0.88), VERMELHO)
        rotulo(ctx, esc, "Problema: cada consulta ao dicionário custa um acesso ao disco.", bx - 110, y + 250, 400, 11, VERMELHO, True)
    ap.slide("problema", "1:30", "Problema: pertence ao conjunto?", s2,
             "Explicar a hifenização: um programa hifeniza palavras por regras, mas 10% das palavras exigem consulta a um dicionário grande em disco. "
             "A pergunta “essa palavra é exceção?” precisa ser respondida para TODAS as 500.000 palavras, e quase sempre a resposta é “não”. "
             "Ir ao disco toda vez é o gargalo. Fonte: exemplo da seção 2 do artigo.")

    # ---------------------------------------------------------------- 3
    def s3(ctx, esc, x, y, w, h):
        pontos(ctx, esc, [
            "Alternativa usual: **tabela hash convencional** (sem erros).",
            "Cada célula guarda a mensagem inteira: **b bits + 1 bit** de “ocupada”.",
            "Há colisões → o tempo cresce se a tabela estiver cheia.",
        ], x, y, 520, 16, 8)
        # células
        cx = x + 570
        rotulo(ctx, esc, "tabela com h células", cx, y, 320, 11, CINZA, True)
        for i in range(8):
            ocup = i in (0, 2, 3, 6)
            ctx.set_source_rgb(*(0.85, 0.9, 1.0) if ocup else (1, 1, 1))
            ctx.rectangle(cx + (i % 4) * 78, y + 22 + (i // 4) * 44, 74, 36)
            ctx.fill_preserve()
            ctx.set_source_rgb(0.3, 0.3, 0.3)
            ctx.set_line_width(0.8)
            ctx.stroke()
            rotulo(ctx, esc, ("1 | " if ocup else "0 | ") + ("mensagem" if ocup else "vazia"), cx + (i % 4) * 78, y + 33 + (i // 4) * 44, 74, 9, PRETO, False, "centro")
        # fórmulas
        caixa(ctx, x, y + 150, 430, 62, "N = n·(b+1)·(T+2) / (T−1)\n(espaço em bits)", 16, (0.93, 0.95, 1.0), AZUL, PRETO, True)
        pontos(ctx, esc, [
            "**n** = mensagens guardadas · **b** = bits por mensagem",
            "**T** = tempo de rejeição: bits examinados até concluir “ausente”",
        ], x, y + 224, 430, 12, 3)
        caixa(ctx, x + 470, y + 150, 418, 100, "Exemplo do artigo: 50.000 palavras com T = 4\n≈ 2.000.000 de bits\n— grande demais para a memória principal da época", 14, (1, 0.9, 0.9), VERMELHO)
    ap.slide("problema", "1:30", "Por que o método usual não basta?", s3,
             "Definir os símbolos ANTES de usá-los: n é o número de mensagens, b o tamanho de cada uma, T o tempo de rejeição (quantos bits olhamos até dizer “não está”). "
             "A tabela convencional precisa guardar a mensagem inteira. Pela fórmula do artigo, só para as 50.000 exceções são ≈ 2 milhões de bits, o que não cabia na memória principal; "
             "restava o disco. Essa é a motivação do artigo.")

    # ---------------------------------------------------------------- 4
    def s4(ctx, esc, x, y, w, h):
        pontos(ctx, esc, [
            "Ideia de Bloom: **trocar certeza por espaço**.",
            "Aceitar uma pequena fração **P''** de **falsos positivos** (“está” quando não está).",
            "Nunca errar no outro sentido: **zero falsos negativos**.",
            "Quem for aceito pelo filtro passa por um **teste secundário** (disco); quem for rejeitado nem precisa.",
        ], x, y, 480, 16, 9)
        bx = x + 540
        caixa(ctx, bx + 80, y, 170, 44, "espaço (N'')", 14, (0.9, 0.94, 1), AZUL, PRETO, True)
        caixa(ctx, bx, y + 120, 160, 44, "tempo de rejeição (T'')", 13, (0.9, 0.94, 1), AZUL, PRETO, True)
        caixa(ctx, bx + 175, y + 120, 160, 44, "erro permitido (P'')", 13, (1, 0.93, 0.85), LARANJA, PRETO, True)
        seta(ctx, bx + 120, y + 44, bx + 70, y + 120, CINZA)
        seta(ctx, bx + 210, y + 44, bx + 255, y + 120, CINZA)
        rotulo(ctx, esc, "Os 3 fatores do artigo:\nmais erro tolerado → bem menos espaço, mesmo tempo de rejeição.", bx - 20, y + 190, 360, 12, PRETO, True)
        rotulo(ctx, esc, "O artigo propõe dois métodos: Método 1 (célula guarda um código de c < b bits) e Método 2 (sem células, só um vetor de bits) — o Filtro de Bloom.", bx - 20, y + 235, 360, 11, CINZA)
    ap.slide("solucao", "0:30", "Ideia central", s4,
             "Deixar claro o contrato do filtro: se responde “não”, é certeza; se responde “sim”, é só provável. Por isso serve quando a maioria das consultas é “não” e existe um teste secundário "
             "barato de acionar poucas vezes. O artigo mostra que aceitar um pouco de erro reduz muito o espaço sem piorar o tempo de rejeição. Vamos ao Método 2.")

    # ---------------------------------------------------------------- 5
    def s5(ctx, esc, x, y, w, h):
        rotulo(ctx, esc, "Vetor de N'' = 24 bits, todos 0 no início:", x, y, 500, 13, PRETO, True)
        desenhar_bits(ctx, x, y + 24, ESTADOS[0], 34, None, True, 14)
        pontos(ctx, esc, [
            "**N''** = quantidade de bits do vetor · **d** = endereços (bits) por mensagem · **n** = mensagens inseridas",
            "Cada mensagem é transformada por **d funções de hash** em d endereços a₁, …, a_d (aqui d = 3).",
        ], x, y + 90, w, 15, 6)
        caixa(ctx, x, y + 175, 420, 80, "INSERIR\nliga (coloca em 1) os d bits da mensagem", 15, (0.9, 0.97, 0.9), VERDE, PRETO, True)
        caixa(ctx, x + 468, y + 175, 420, 80, "CONSULTAR\nlê os d bits: algum 0 → rejeita; todos 1 → aceita", 15, (0.9, 0.94, 1), AZUL, PRETO, True)
    ap.slide("solucao", "1:00", "Representação: um vetor de bits e d endereços", s5,
             "Mostrar que não existem células: é só um vetor de bits. Explicar N'', d e n antes de qualquer fórmula. Dizer que “d funções de hash” significa: d números diferentes calculados a partir da mensagem, "
             "cada um virando uma posição no vetor. Na nossa implementação, os d endereços saem de dois hashes (FNV-1a e DJB2) combinados — simplificação documentada no relatório.")

    # ---------------------------------------------------------------- 6
    def s6(ctx, esc, x, y, w, h):
        rotulos = ["início", "inserir gato → bits 4, 9, 14", "inserir cao → bits 2, 11, 20", "inserir pato → bits 7, 13, 22"]
        for i in range(4):
            yy = y + i * 68
            rotulo(ctx, esc, rotulos[i], x, yy, 300, 12, PRETO, True)
            dest = {p: LARANJA_CLARO for p in NOVOS[i]} if NOVOS[i] else {}
            desenhar_bits(ctx, x + 300, yy - 2, ESTADOS[i], 24, dest, True, 11)
        rotulo(ctx, esc, "laranja = bits que acabaram de ser ligados · azul = ligados antes", x + 300, y + 4 * 68 - 4, 580, 10, CINZA)
    ap.slide("solucao", "1:30", "Exemplo passo a passo: inserção (N'' = 24, d = 3)", s6,
             "Seguir linha por linha: gato liga 4, 9 e 14; cao liga 2, 11 e 20; pato liga 7, 13 e 22. Nesta amostra nenhum bit foi ligado duas vezes, então ficam 9 bits em 1. "
             "Se duas palavras ligarem o mesmo bit, ele simplesmente continua 1 — um bit nunca volta a 0 (invariante). Estes valores são a saída real do programa `make exemplo`.")

    # ---------------------------------------------------------------- 7
    def s7(ctx, esc, x, y, w, h):
        rotulo(ctx, esc, "Vetor atual:", x, y, 400, 12, PRETO, True)
        desenhar_bits(ctx, x + 130, y - 2, ESTADOS[3], 22, None, True, 10)
        consultas = [
            ("gato", [(4, 1), (9, 1), (14, 1)], "ACEITA — está no conjunto (3 bits lidos)", VERDE),
            ("peixe", [(6, 0)], "REJEITADA — bit 6 é 0 (1 bit lido): certeza de que não está", VERMELHO),
            ("galo", [(4, 1), (19, 0)], "REJEITADA — bit 19 é 0 (2 bits lidos)", VERMELHO),
            ("coelho", [(7, 1), (9, 1), (11, 1)], "ACEITA — mas NÃO foi inserida: FALSO POSITIVO", LARANJA),
        ]
        for i, (nome, lidos, texto, cor) in enumerate(consultas):
            yy = y + 52 + i * 52
            rotulo(ctx, esc, "consultar %s" % nome, x, yy + 2, 125, 12, PRETO, True)
            dest = {p: (VERDE_CLARO if v else VERMELHO_CLARO) for p, v in lidos}
            desenhar_bits(ctx, x + 130, yy - 2, ESTADOS[3], 22, dest, False, 10)
            rotulo(ctx, esc, texto, x + 130 + 22 * 24 + 14, yy - 2, 220, 11, cor, True)
        rotulo(ctx, esc, "verde = lido e vale 1 · vermelho = lido e vale 0 (a leitura para aqui)", x, y + 52 + 4 * 52 + 2, 700, 10, CINZA)
    ap.slide("solucao", "1:30", "Exemplo passo a passo: consulta", s7,
             "gato: os três bits valem 1 → aceita, correto. peixe: o primeiro bit lido já vale 0 → rejeita com certeza lendo só 1 bit. galo: o 1º bit vale 1, o 2º vale 0 → rejeita. "
             "coelho: seus três bits (7, 9, 11) foram ligados por pato, gato e cao → o filtro aceita, mas coelho nunca foi inserido: é o falso positivo, erro permitido. "
             "Por isso o filtro nunca erra dizendo “não”, mas pode errar dizendo “sim”.")

    # ---------------------------------------------------------------- 8
    def s8(ctx, esc, x, y, w, h):
        caixa(ctx, x, y, 430, 52, "φ'' = (1 − d/N'')ⁿ  ≈  e^(−n·d/N'')", 17, (0.93, 0.95, 1), AZUL, PRETO, True)
        rotulo(ctx, esc, "fração de bits que continuam 0 depois de n inserções", x, y + 58, 430, 11, CINZA)
        caixa(ctx, x + 458, y, 430, 52, "P'' = (1 − φ'')^d", 17, (1, 0.93, 0.85), LARANJA, PRETO, True)
        rotulo(ctx, esc, "chance de uma mensagem ausente ter os d bits em 1 (falso positivo)", x + 458, y + 58, 430, 11, CINZA)
        caixa(ctx, x, y + 100, 430, 52, "T'' ≈ 1/φ''", 17, (0.9, 0.97, 0.9), VERDE, PRETO, True)
        rotulo(ctx, esc, "bits lidos, em média, até achar um 0 e rejeitar", x, y + 158, 430, 11, CINZA)
        pontos(ctx, esc, [
            "Hipótese: os hashes se comportam como **uniformes e independentes**.",
            "No exemplo: φ'' = (1 − 3/24)³ ≈ 0,67 (medido 0,625); P'' = (1 − 0,67)³ ≈ 0,04.",
            "Quanto mais bits viram 1, menor φ'' e maior P''.",
        ], x + 458, y + 100, 430, 13, 5)
    ap.slide("solucao", "1:30", "Análise: quanto o filtro erra e quanto custa?", s8,
             "Explicar a ideia, sem demonstrar: cada inserção tem d chances de ligar um bit específico, então a chance de um bit continuar 0 depois de n inserções é (1 − d/N'')^n. "
             "Chamamos isso de φ''. Um falso positivo acontece quando os d bits de uma mensagem ausente caem todos em posições já ligadas: (1 − φ'')^d. "
             "T'' é o tempo de rejeição, medido em bits lidos. Hipótese essencial: hashes uniformes e independentes. A demonstração completa não faz parte do escopo.")

    # ---------------------------------------------------------------- 9
    def s9(ctx, esc, x, y, w, h):
        pontos(ctx, esc, [
            "Para um P'' desejado, o filtro é **menor** quando **metade dos bits vale 1**: φ'' = 1/2 (T'' ≈ 2).",
            "Então: **d = log₂(1/P'')** e **N'' ≈ 1,44 · n · log₂(1/P'')** bits.",
            "Cada vez que P'' cai pela metade, entram só +1,44 bits por chave.",
        ], x, y, 430, 15, 8)
        linhas = [["P''", "d", "bits/chave"]] + [[frac(p), str(int(round(-math.log2(p)))), pt(-math.log2(p) * 1.4427, 2)] for p in P_VALORES]
        yy = y + 190
        for i, linha in enumerate(linhas):
            for j, c in enumerate(linha):
                ctx.set_source_rgb(*(AZUL if i == 0 else ((0.96, 0.96, 0.98) if i % 2 else (1, 1, 1))))
                ctx.rectangle(x + j * 90, yy + i * 17, 90, 17)
                ctx.fill()
                rotulo(ctx, esc, c, x + j * 90, yy + 2 + i * 17, 90, 10.5, (1, 1, 1) if i == 0 else PRETO, i == 0, "centro")
        graf_bits(ctx, x + 450, y, 440, 300, 10)
    ap.slide("solucao", "1:00", "Ponto ótimo: φ'' = 1/2", s9,
             "O artigo mostra que, para um erro P'' fixo, o espaço é mínimo quando metade do vetor está ligada. Daí saem as duas regras de projeto: d = log₂(1/P'') e N'' ≈ 1,44·n·log₂(1/P''). "
             "O gráfico compara com o método convencional (b = 64 e T = 4 → 130 bits por chave): com P'' = 1/16 o filtro usa ≈ 5,8 bits por chave. "
             "A nossa função `filtro_criar_otimo` aplica exatamente estas fórmulas.")

    # ---------------------------------------------------------------- 10
    def s10(ctx, esc, x, y, w, h):
        pontos(ctx, esc, [
            "Hifenização: 500.000 palavras, 50.000 exceções.",
            "Convencional: ≈ **2.000.000 bits**.",
            "Bloom com P'' = 1/16: **< 300.000 bits** (≈ 85% menos).",
            "Só ≈ 78.000 das 500.000 consultas vão ao disco → **84,4% dos acessos evitados**.",
            "Nossa simulação: N'' = 288.540 bits e 84,4% (resultado reproduzido).",
        ], x, y, 410, 15, 8)
        graf_hif(ctx, x + 430, y, 460, 300, 10)
    ap.slide("critica", "1:00", "Resultado do artigo (e da nossa simulação)", s10,
             "Aplicar as fórmulas ao caso do artigo: com P'' = 1/16 só vai ao disco quem o filtro aceita: as 50.000 exceções verdadeiras mais 1/16 das 450.000 palavras normais, ≈ 78.000 consultas. "
             "Ou seja, 84,4% menos acessos. Na nossa simulação (simples contagem de acessos, o disco não foi implementado) obtivemos o mesmo percentual. O gráfico compara com a Tabela I do artigo.")

    # ---------------------------------------------------------------- 11
    def s11(ctx, esc, x, y, w, h):
        cab = ["", "Hash convencional", "Método 1 (código de c bits)", "Método 2 (Filtro de Bloom)"]
        linhas = [
            ["O que guarda", "mensagem inteira (b bits + 1)", "código com c < b bits por célula", "só bits ligados (d por mensagem)"],
            ["Falso positivo", "não", "sim (P')", "sim (P'')"],
            ["Falso negativo", "não", "não", "não"],
            ["Espaço mínimo", "n(b+1)(T+2)/(T−1)", "menor que o convencional", "≈ 1,44·n·log₂(1/P'')"],
            ["Segundo o artigo", "referência", "intermediário", "melhor em quase toda a faixa"],
        ]
        larg = [150, 230, 250, 258]
        for i, linha in enumerate([cab] + linhas):
            xx = x
            for j, c in enumerate(linha):
                ctx.set_source_rgb(*(AZUL if i == 0 else ((0.94, 0.96, 1.0) if i % 2 else (1, 1, 1))))
                ctx.rectangle(xx, y + i * 30, larg[j], 30)
                ctx.fill()
                rotulo(ctx, esc, c, xx + 4, y + 8 + i * 30, larg[j] - 8, 11.5, (1, 1, 1) if i == 0 else PRETO, i == 0 or j == 0 or (i == 5 and j == 3), "centro")
                xx += larg[j]
        yy = y + 195
        rotulo(ctx, esc, "Vantagens", x, yy, 420, 14, VERDE, True)
        pontos(ctx, esc, ["muito menos espaço", "inserir e consultar custam O(d) acessos, d independente de n", "rejeição rápida (≈ 2 bits lidos)"], x, yy + 20, 420, 12.5, 3)
        rotulo(ctx, esc, "Limitações", x + 470, yy, 420, 14, VERMELHO, True)
        pontos(ctx, esc, ["falsos positivos nunca somem (precisa de teste secundário)", "não remove chaves; precisa estimar n antes", "hashes ruins ou n acima do previsto aumentam P''"], x + 470, yy + 20, 418, 12.5, 3)
    ap.slide("critica", "1:30", "Análise crítica e comparação", s11,
             "Comparar com a alternativa conhecida: a tabela hash convencional é exata mas guarda a mensagem inteira. O Método 1 do artigo já economiza espaço guardando só um código, mas o Método 2 vai além. "
             "Custos: inserir e consultar são O(d) acessos ao vetor (mais o custo do hash sobre a chave), com d = log₂(1/P'') independente de n. Hipóteses: hashes uniformes e independentes, n conhecido. "
             "Limitações principais: sem remoção, falso positivo irredutível, n precisa ser estimado.")

    # ---------------------------------------------------------------- 12
    def s12(ctx, esc, x, y, w, h):
        pontos(ctx, esc, [
            "10 testes automáticos: **zero falsos negativos**, entradas inválidas, filtro vazio, repetidos, saturação.",
            "Experimento: n = 10⁴, 10⁵ e 10⁶; P'' de 1/2 a 1/64; 2 tipos de chaves; **10 repetições**.",
            "φ'' medido = 0,500; P'' medido ≈ alvo em todas as configurações.",
            "Chaves sequenciais variam mais entre repetições (hash não é perfeitamente uniforme).",
        ], x, y, 410, 14, 7)
        graf_p_emp(ctx, x + 430, y, 460, 300, tam=10)
    ap.slide("critica", "0:30", "Verificação: a teoria bate com a implementação?", s12,
             "Mostrar rapidamente que o que as fórmulas prevêem foi confirmado na implementação em C: o erro medido (eixo vertical) coincide com o alvo (eixo horizontal) para os três tamanhos de n. "
             "Dizer que há dois tipos de resultado: erros permitidos (falsos positivos) e defeitos (falso negativo, falha de memória), e que só os primeiros apareceram. Detalhes no relatório de testes.")

    # ---------------------------------------------------------------- 13
    def s13(ctx, esc, x, y, w, h):
        cards = [
            ("ARTIGO", AZUL, "Hifenização com dicionário de exceções",
             "Mantém na memória um filtro das 10% de palavras excepcionais; o disco só é acessado para palavras aceitas. (Bloom, 1970, seção 2)"),
            ("OUTRA FONTE", ROXO, "Bancos de dados em disco (Bigtable)",
             "Antes de ler um arquivo em disco, pergunta-se ao filtro se ele pode conter a chave; evita leituras inúteis. (Chang et al., 2006)"),
            ("PROPOSTA DO GRUPO (hipótese)", VERDE, "Bloqueio de sites maliciosos no navegador",
             "Filtro local das URLs perigosas: URL rejeitada abre direto; URL aceita é confirmada em uma lista completa. Será detalhada no próximo slide."),
        ]
        cw = (w - 2 * 20) / 3
        for i, (tag, cor, tit, txt) in enumerate(cards):
            cx = x + i * (cw + 20)
            ctx.set_source_rgb(0.97, 0.97, 0.97)
            ctx.rectangle(cx, y, cw, 270)
            ctx.fill()
            ctx.set_source_rgb(*cor)
            ctx.rectangle(cx, y, cw, 6)
            ctx.fill()
            rotulo(ctx, esc, tag, cx + 10, y + 16, cw - 20, 10, cor, True)
            yy = y + 36 + rotulo(ctx, esc, tit, cx + 10, y + 36, cw - 20, 18, PRETO, True)
            rotulo(ctx, esc, txt, cx + 10, yy + 14, cw - 20, 15, PRETO)
    ap.slide("aplic", "1:00", "Aplicações possíveis (e de onde vem cada uma)", s13,
             "Distinguir as origens: (1) a hifenização é a aplicação apresentada pelos autores; (2) o uso em armazenamento em disco vem de outra fonte — o artigo do Bigtable (Chang et al., 2006) descreve filtros de Bloom para evitar leituras de disco; "
             "(3) o bloqueio de sites no navegador é uma ideia do grupo: é uma hipótese fundamentada, NÃO um resultado demonstrado. A seguir, a terceira em profundidade.")

    # ---------------------------------------------------------------- 14
    def s14(ctx, esc, x, y, w, h):
        linhas = [
            ("Dados de entrada", "lista de URLs maliciosas (hipótese: n = 1.000.000) e a URL clicada pelo usuário"),
            ("Operações", "inserir (ao receber/atualizar a lista) · consultar (a cada clique)"),
            ("Contexto de uso", "navegador com pouca memória; a lista completa fica em um servidor remoto"),
            ("Benefício esperado", "P'' = 1/64 → N'' ≈ 8,7 Mbit ≈ 1,1 MB (lista exata ≈ 50 MB, supondo 50 bytes/URL). Só ≈ 1,6% dos cliques em sites seguros exigem confirmação."),
            ("Limitação", "não remove URL que deixou de ser perigosa → refazer o filtro; falso positivo exige a verificação completa"),
            ("Alternativa", "conjunto hash exato em memória (sem erro, ≈ 50× mais memória) ou consulta remota a cada clique (latência e privacidade)"),
        ]
        yy = y
        for nome, txt in linhas:
            alt = max(esc.altura(txt, 700, 12.5, 1.2), 22) + 8
            ctx.set_source_rgb(*(0.94, 0.97, 0.94))
            ctx.rectangle(x, yy, 170, alt)
            ctx.fill()
            ctx.set_source_rgb(0.98, 0.98, 0.98)
            ctx.rectangle(x + 170, yy, w - 170, alt)
            ctx.fill()
            rotulo(ctx, esc, nome, x + 8, yy + 5, 156, 12.5, VERDE, True)
            rotulo(ctx, esc, txt, x + 180, yy + 5, 700, 12.5, PRETO)
            yy += alt + 4
        rotulo(ctx, esc, "Hipótese fundamentada (cálculo pelas fórmulas do artigo) — não é um sistema construído nem medido.", x, yy + 4, w, 10.5, CINZA, True)
    ap.slide("aplic", "3:00", "Aplicação em profundidade: bloquear sites maliciosos", s14,
             "Percorrer a tabela: dados, operações, contexto, benefício, limitação e comparação. A conta usa as fórmulas do artigo: n = 1 milhão e P'' = 1/64 dão ≈ 8,7 milhões de bits (≈ 1,1 MB). "
             "O tamanho da lista exata (≈ 50 MB) é uma SUPOSIÇÃO (50 bytes por URL). A taxa de confirmação extra (≈ 1,6%) é a taxa de falsos positivos. Por que é adequada: quase todo clique é em site seguro (rejeição rápida) e existe teste secundário. "
             "Limitação: não remove. Alternativas: conjunto exato (mais memória) ou consulta remota (latência e privacidade).")

    # ---------------------------------------------------------------- 15
    def s15(ctx, esc, x, y, w, h):
        pontos(ctx, esc, [
            "**Contribuição:** aceitar uma pequena taxa de falsos positivos reduz muito o espaço, sem piorar o tempo de rejeição.",
            "**Como funciona:** vetor de N'' bits + d hashes; inserir liga d bits; consultar lê até o primeiro 0.",
            "**Quando usar:** quase todas as consultas são de itens ausentes; falso positivo é tolerável e há um teste secundário; n é conhecido; não é preciso remover.",
            "**Ponto ótimo:** φ'' = 1/2, d = log₂(1/P''), N'' ≈ 1,44·n·log₂(1/P'') bits.",
            "**Na prática:** nossa implementação em C confirmou as fórmulas (zero falsos negativos; P'' medido ≈ alvo).",
        ], x, y, w, 17, 12)
    ap.slide("sintese", "1:00", "Síntese", s15,
             "Fechar com a mensagem principal: o filtro não substitui a busca exata, ele a evita na maioria dos casos. Repetir as condições de uso. "
             "Convidar às perguntas. Todos os integrantes devem estar prontos para explicar qualquer parte (problema, exemplo, fórmulas, aplicações, código, testes).")

    # ---------------------------------------------------------------- 16
    def s16(ctx, esc, x, y, w, h):
        pontos(ctx, esc, [
            REF_BLOOM,
            "Chang, F. et al. (2006). Bigtable: a distributed storage system for structured data. OSDI 2006 (uso de filtros de Bloom para evitar leituras em disco).",
            "Fowler, G.; Noll, L. C.; Vo, K.-P. FNV hash. http://www.isthe.com/chongo/tech/comp/fnv/ · Bernstein, D. J. DJB2. http://www.cse.yorku.ca/~oz/hash.html",
            "Kirsch, A.; Mitzenmacher, M. (2006). Less hashing, same performance: building a better Bloom filter. ESA 2006 (hash duplo).",
            "Implementação, testes e experimento do grupo: repositório do trabalho (src/, tests/, resultados/).",
        ], x, y, w, 13, 9)
    ap.slide("sintese", "—", "Referências", s16,
             "Slide de referência para consulta durante as perguntas; não é lido em voz alta. As aplicações (2) e (3) do slide 13 devem ser identificadas como outra fonte e proposta do grupo, respectivamente.")
    ap.fim()
