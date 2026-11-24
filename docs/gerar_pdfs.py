# -*- coding: utf-8 -*-
"""
Gera os 3 PDFs do trabalho (a partir dos resultados reais em resultados/):
  docs/relatorio.pdf   - relatório técnico (3 páginas de conteúdo + referências)
  docs/testes.pdf      - relatório de testes (correção, memória e experimento)
  docs/slides.pdf      - roteiro dos slides do seminário, uma página por slide
Uso: python3 docs/gerar_pdfs.py   (ou: make pdfs)
"""
import csv
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdf_base import *  # noqa: E402,F401,F403

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(RAIZ, "resultados")
DOCS = os.path.join(RAIZ, "docs")

INTEGRANTES = ["Giovanni Timonez", "Pedro Henrique Holzmeier Schaefer", "Rafael Knebel", "Verônica Martini", "Vitor Lago"]
REF_BLOOM = "Bloom, B. H. (1970). Space/time trade-offs in hash coding with allowable errors. Communications of the ACM, 13(7), 422–426."


# ---------------------------------------------------------------------------
# Dados
# ---------------------------------------------------------------------------
def ler_csv(nome):
    with open(os.path.join(RES, nome), newline="", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f, delimiter=";"))
    for l in linhas:
        for k, v in l.items():
            try:
                l[k] = float(v)
            except ValueError:
                pass
    return linhas


def ler_texto(nome):
    with open(os.path.join(RES, nome), encoding="utf-8") as f:
        return f.read()


def comando(*args):
    try:
        return subprocess.run(args, capture_output=True, text=True).stdout.strip().split("\n")[0]
    except Exception:
        return "?"


def ambiente():
    cpu = "?"
    try:
        for linha in open("/proc/cpuinfo"):
            if linha.startswith("model name"):
                cpu = linha.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    return {"cpu": cpu, "gcc": comando("gcc", "--version"), "so": comando("uname", "-sr"),
            "flags": "-Wall -Wextra -std=c11 -O2 -D_POSIX_C_SOURCE=200809L"}


def pt(x, casas=2):
    """Número com vírgula decimal."""
    return ("%.*f" % (casas, x)).replace(".", ",")


def milhar(n):
    return "{:,}".format(int(n)).replace(",", ".")


def frac(p):
    return "1/%d" % round(1 / p)


EXP = ler_csv("experimento.csv")
HIF = ler_csv("hifenizacao.csv")
ENV = ambiente()
ARTIGO_TABELA = {  # Tabela I do artigo (traduzida): P -> (bits, economia %)
    0.5: (72800, 45.0), 0.25: (145600, 67.5), 0.125: (218400, 78.7),
    0.0625: (291200, 84.4), 0.03125: (364000, 87.2), 0.015625: (509800, 88.5)}
P_VALORES = [0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625]


def linha_exp(dist, n, p):
    for l in EXP:
        if l["distribuicao"] == dist and int(l["n"]) == n and abs(l["P_alvo"] - p) < 1e-9:
            return l
    raise KeyError((dist, n, p))


def t_exato(l):
    """T'' para consultas ausentes com d finito: (1-(1-φ)^d)/φ."""
    phi = l["phi_teorico"]
    return (1 - (1 - phi) ** l["d"]) / phi


def resumo_z(dist):
    """Quantas configurações têm P emp a menos de 2 e 3 erros-padrão de P teórico."""
    z = []
    for l in EXP:
        if l["distribuicao"] == dist:
            ep = l["P_dp"] / math.sqrt(10)
            z.append(abs(l["P_emp"] - l["P_teorico"]) / ep if ep > 0 else 0)
    return sum(1 for v in z if v < 2), sum(1 for v in z if v < 3), len(z), max(z)


def maior_desvio_rel(dist):
    return max(abs(l["P_emp"] - l["P_teorico"]) / l["P_teorico"] for l in EXP if l["distribuicao"] == dist)


# ---------------------------------------------------------------------------
# Gráficos reutilizados
# ---------------------------------------------------------------------------
def rotulo_p(v):
    return frac(v)


def graf_p_emp(ctx, x, y, w, h, dist="aleatoria", tam=7.5):
    cores = {10000: AZUL, 100000: VERDE, 1000000: LARANJA}
    series = []
    for n in (10000, 100000, 1000000):
        pts = [(p, linha_exp(dist, n, p)["P_emp"]) for p in P_VALORES]
        series.append({"label": "n = 10" + {4: "⁴", 5: "⁵", 6: "⁶"}[round(math.log10(n))], "cor": cores[n], "pontos": pts})
    grafico(ctx, x, y, w, h, series, "P'' alvo (fórmula do artigo)", "P'' medido",
            (0.012, 0.65), (0.012, 0.65), P_VALORES, P_VALORES, True, True, rotulo_p, rotulo_p,
            titulo="Erro medido × erro alvo", tam=tam, linha_ref=[(0.012, 0.012), (0.65, 0.65)])


def graf_bits(ctx, x, y, w, h, tam=7.5):
    pts = [(p, linha_exp("aleatoria", 1000000, p)["bits_por_chave"]) for p in P_VALORES]
    conv = [(p, 130.0) for p in (0.012, 0.65)]
    grafico(ctx, x, y, w, h,
            [{"label": "Filtro de Bloom", "cor": AZUL, "pontos": pts},
             {"label": "convencional (b=64, T=4)", "cor": VERMELHO, "pontos": conv, "marcador": False}],
            "P'' alvo", "bits por chave", (0.012, 0.65), (1, 200), P_VALORES, [1, 2, 5, 10, 20, 50, 100, 200],
            True, True, rotulo_p, lambda v: str(int(v)), titulo="Espaço por chave", tam=tam)


def graf_t(ctx, x, y, w, h, tam=7.5):
    pts = [(p, linha_exp("aleatoria", 1000000, p)["T_emp"]) for p in P_VALORES]
    teo = [(p, t_exato(linha_exp("aleatoria", 1000000, p))) for p in P_VALORES]
    art = [(p, 2.0) for p in (0.012, 0.65)]
    grafico(ctx, x, y, w, h,
            [{"label": "T'' medido", "cor": AZUL, "pontos": pts},
             {"label": "fórmula exata", "cor": VERDE, "pontos": teo, "marcador": False, "tracejado": True},
             {"label": "artigo (= 2)", "cor": VERMELHO, "pontos": art, "marcador": False}],
            "P'' alvo", "bits lidos", (0.012, 0.65), (0.8, 2.2), P_VALORES, [1, 1.25, 1.5, 1.75, 2],
            True, False, rotulo_p, lambda v: pt(v, 2), titulo="Tempo de rejeição T'' (n = 10⁶)", tam=tam)


def graf_tempo(ctx, x, y, w, h, tam=7.5):
    series = []
    cores = {0.5: ROXO, 0.0625: AZUL, 0.015625: VERMELHO}
    for p, cor in cores.items():
        pts = [(n, linha_exp("aleatoria", n, p)["ns_consultar"]) for n in (10000, 100000, 1000000)]
        series.append({"label": "P''=%s (d=%d)" % (frac(p), int(linha_exp("aleatoria", 10000, p)["d"])), "cor": cor, "pontos": pts})
    grafico(ctx, x, y, w, h, series, "n (chaves inseridas)", "ns / consulta", (7000, 1.5e6), (0, 100),
            [1e4, 1e5, 1e6], [0, 25, 50, 75, 100], True, False, lambda v: "10^%d" % round(math.log10(v)),
            lambda v: str(int(v)), titulo="Tempo de consulta × n", tam=tam)


def graf_hif(ctx, x, y, w, h, tam=7.5):
    nossa = [(l["P_alvo"], 100 * l["economia_acessos"]) for l in HIF]
    art = [(p, ARTIGO_TABELA[p][1]) for p in P_VALORES]
    grafico(ctx, x, y, w, h,
            [{"label": "esta implementação", "cor": AZUL, "pontos": nossa},
             {"label": "Tabela I do artigo", "cor": VERMELHO, "pontos": art, "tracejado": True}],
            "P'' alvo", "acessos evitados (%)", (0.012, 0.65), (40, 92), P_VALORES, [40, 50, 60, 70, 80, 90],
            True, False, rotulo_p, lambda v: str(int(v)), titulo="Caso da hifenização (500.000 palavras)", tam=tam)


# ---------------------------------------------------------------------------
# 1) RELATÓRIO TÉCNICO (3 páginas de conteúdo + 1 página de referências)
# ---------------------------------------------------------------------------
def _fig_exemplo_relatorio(ctx, x, y, w, h):
    """Diagrama compacto do exemplo didático (N=24, d=3) para o relatório."""
    esc = Escritor(ctx)
    estado = "001010010101011000001010"
    esc.desenhar("Vetor após inserir 'gato' (4, 9, 14), 'cao' (2, 11, 20) e 'pato' (7, 13, 22):",
                 x, y, w, 7.8, PRETO, 1.2, negrito=True)
    desenhar_bits(ctx, x + 12, y + 13, estado, 19.5, {7: (1, 0.82, 0.55), 9: (1, 0.82, 0.55), 11: (1, 0.82, 0.55)}, True, 8.2)
    esc.desenhar("• Consulta 'peixe' (6, 14, 22): bit 6 = 0 → REJEITADA no 1º bit (ausência garantida).   "
                 "• Consulta 'coelho' (7, 9, 11, em laranja): todos 1 → ACEITA (falso positivo).",
                 x, y + 46, w, 7.6, CINZA, 1.25)


def gerar_relatorio():
    d = Documento(os.path.join(DOCS, "relatorio.pdf"), "Relatório técnico · Filtro de Bloom · ED2 (GEX1210) · UFFS Chapecó", margem=42)
    d.titulo("Filtro de Bloom (Método 2 de Bloom, 1970): solução, implementação em C e avaliação",
             "Estruturas de Dados II (GEX1210) · UFFS Campus Chapecó · Relatório Técnico · Novembro de 2026")
    d.paragrafo("**Integrantes:** " + "; ".join(n + " (matrícula: ____)" for n in INTEGRANTES) + ".", 8.2, depois=1.5)
    d.paragrafo("**Artigo estudado:** " + REF_BLOOM, 8.2, depois=3)

    # ---- SEÇÃO 1 ----
    d.secao("1. Problema, motivação e escopo implementado", 10.5)
    d.paragrafo(
        "O artigo de Bloom (1970) trata do problema de testar, uma a uma, se mensagens pertencem a um conjunto fixo de **n** itens quando "
        "**a grande maioria das consultas é negativa** (elementos ausentes) e uma estrutura exata não cabe na memória principal (RAM). "
        "Na abordagem **convencional** (tabela hash aberta sem erros), cada célula armazena a chave inteira (**b** bits) mais 1 bit de estado, "
        "exigindo N = n·(b+1)·(T+2)/(T−1) bits — o que força o uso de disco lento quando n ou b são grandes. O **Método 1** reduz as células "
        "para códigos de c < b bits, aceitando erros de comissão. O **Método 2 (Filtro de Bloom)** elimina totalmente as células e adota um "
        "vetor único de **N''** bits individuais: ao tolerar uma fração controlada **P''** de **falsos positivos** e garantir **zero falsos negativos**, "
        "reduz drasticamente o espaço sem degradar o **tempo de rejeição T''** (bits examinados até descartar uma chave ausente).",
        8.6, depois=2.5, entrelinha=1.24)
    d.lista([
        "**Núcleo implementado (`include/filtro_bloom.h`, `src/filtro_bloom.c`):** estrutura `FiltroBloom` com `filtro_criar`, "
        "`filtro_criar_otimo` (dimensionamento no ponto ótimo φ'' = 1/2), `filtro_inserir`, `filtro_consultar` (com contagem opcional "
        "`bits_lidos` para medir T''), `filtro_destruir`, `filtro_endereco`, `filtro_contar_uns`, `filtro_phi_empirico`, `filtro_phi_teorico` e `filtro_erro_teorico`.",
        "**Módulos de verificação (`tests/`):** `teste_corretude.c` (10 asserções automatizadas), `exemplo.c` (traço didático bit a bit com 24 bits) "
        "e `experimento.c` (bateria estatística variando n, P'' e distribuição de chaves + simulação da aplicação de hifenização do artigo).",
        "**Simplificações identificadas e decisões:** (i) chaves são strings C terminadas em `'\\0'`; (ii) os d endereços são gerados por **hash duplo** "
        "(FNV-1a 64 bits + DJB2 64 bits com avalanche final: `h1 + i·passo mod N''`, forçando `passo >= 1`) em vez de d funções independentes; "
        "(iii) os d endereços de uma mesma chave podem coincidir; (iv) o dicionário em disco da hifenização é **simulado** por contagem de aceitações; "
        "(v) o Método 1 é tratado apenas analiticamente (não implementado). **Fora do escopo:** remoção, redimensionamento, persistência e hashes criptográficos.",
    ], 8.3, depois=1.4, entrelinha=1.22)

    # ---- SEÇÃO 2 ----
    d.secao("2. Solução, invariantes e correspondência com o artigo", 10.5)
    d.paragrafo(
        "O filtro é um vetor de **N''** bits empacotados em `⌈N''/8⌉` bytes (`calloc` zera tudo na criação). O bit na posição `p` reside no byte `p/8`, "
        "deslocamento `p%8` (`ligar_bit` aplica `|=`; `ler_bit` isola com `>>` e `& 1`). Para **inserir** x, calculam-se d endereços e ligam-se esses bits. "
        "Para **consultar** x, testam-se os d endereços em sequência: ao primeiro 0 encontrado, rejeita-se imediatamente (**certeza de ausência**); se todos "
        "valerem 1, aceita-se (**pertence ou falso positivo**). Após n inserções, a fração esperada de bits em 0 é **φ'' = (1 − d/N'')ⁿ ≈ e^(−nd/N'')**, "
        "a taxa esperada de falsos positivos é **P'' = (1 − φ'')^d** e o tempo esperado de rejeição converge para **T'' ≈ 1/φ''**. Minimiza-se o espaço "
        "normalizado S'' = N''/(−n·log₂P'') exatamente quando **φ'' = 1/2** (metade dos bits em 1, T'' = 2), resultando em **S'' = log₂(e) ≈ 1,44**, "
        "**d = ⌈−log₂(P'')⌉** e **N'' = ⌈n·(−log₂P'')·log₂(e)⌉**.",
        8.6, depois=3, entrelinha=1.24)
    d.figura(62, _fig_exemplo_relatorio)
    d.tabela(["Símbolo no artigo", "Identificador no código C", "Significado e relação matemática"], [
        ["N''", "`total_bits`", "Tamanho do vetor em bits (alocados `⌈N''/8⌉` bytes em `vetor_de_bits`)"],
        ["d", "`quantidade_hashes`", "Endereços por chave; no ponto ótimo: `d = ⌈−log₂(P'')⌉`"],
        ["n", "`quantidade_inseridos`", "Total de inserções realizadas no filtro"],
        ["φ'' = (1 − d/N'')ⁿ", "`filtro_phi_empirico` / `_teorico`", "Proporção de bits em 0 (medida varrendo o vetor vs teórica)"],
        ["P'' = (1 − φ'')^d", "`filtro_erro_teorico`", "Probabilidade esperada de falso positivo para chave ausente"],
        ["T'' ≈ 1/φ''", "`*bits_lidos` em `filtro_consultar`", "Número de bits examinados até rejeitar (ou d se aceita)"],
        ["Ponto ótimo (φ'' = 1/2)", "`filtro_criar_otimo(n, erro)`", "`d = ⌈−log₂(erro)⌉`; `N'' = ⌈n · (−log₂(erro)) · log₂(e)⌉`"],
    ], [2.4, 3.1, 4.7], 7.4)
    d.paragrafo(
        "**Invariantes estruturais:** **I1 (Monotonicidade):** um bit 1 jamais retorna a 0 (não há remoção). **I2 (Zero falsos negativos):** após inserir x, "
        "seus d bits valem 1 e nunca são desligados; logo `filtro_consultar(f, x)` sempre retorna `true`. **I3 (Certeza na rejeição):** se ao menos um dos d bits "
        "de x vale 0, x nunca foi inserido; o retorno `false` é exato, enquanto `true` é probabilístico.",
        8.4, depois=2.5, entrelinha=1.23)

    # ---- PÁGINA 2: COMPLEXIDADE + TESTES + EXPERIMENTO (MÉTODO E TABELA) ----
    d.nova_pagina()
    d.secao("3. Análise de complexidade, parâmetros e hipóteses", 10.5)
    d.paragrafo(
        "Sejam **|k|** o comprimento da chave em bytes, **n** o número de elementos esperados, **P''** o erro alvo e **d = ⌈log₂(1/P'')⌉** (constante para P'' fixo, **independente de n**).",
        8.5, depois=2)
    d.tabela(["Operação", "Tempo", "Espaço adicional / estrutura", "Justificativa técnica"], [
        ["`filtro_criar`", "O(N''/8) = O(n·log(1/P''))", "⌈N''/8⌉ bytes (≈ 1,44·n·log₂(1/P'') bits)", "`calloc` zera toda a memória alocada"],
        ["`filtro_criar_otimo`", "O(N''/8)", "O(n·log(1/P'')) bits", "Calcula d e N'' em O(1) e delega para `filtro_criar`"],
        ["`filtro_inserir`", "O(|k| + d)", "O(1)", "FNV-1a e DJB2 percorrem os |k| bytes; laço de d escritas de bit"],
        ["`filtro_consultar`", "Pior: O(|k| + d); Esp. rej.: O(|k| + 1/φ'')", "O(1)", "Para no 1º bit 0 (em φ''=0,5 lê ≈ 2 bits em média)"],
        ["`filtro_phi_empirico`", "O(N'')", "O(1)", "Função de inspeção que varre todos os N'' bits (não usada em produção)"],
        ["Comparação espaço", "—", "Bloom: ≈ 1,44·log₂(1/P'') bits/chave", "Convencional: (b+1)·(T+2)/(T−1) bits/chave (130 bits p/ b=64, T=4)"],
    ], [2.1, 2.7, 2.7, 3.3], 7.3)
    d.paragrafo(
        "**Hipóteses da análise:** (H1) os dois hashes combinados aproximam distribuição uniforme e independente sobre `{0,…,N''−1}`; "
        "(H2) chaves consultadas não são escolhidas por um adversário para forçar colisões; (H3) o número real de inserções não excede n planejado "
        "(exceder n reduz φ'' e eleva P'' exponencialmente, como verificado em T8); (H4) acessos à memória têm custo unitário na análise assintótica "
        "(efeitos reais de cache L1/L2/L3 aparecem nas medições empíricas de tempo).",
        8.4, depois=3, entrelinha=1.23)

    d.secao("4. Método e resultados dos testes e experimento", 10.5)
    d.subsecao("4.1 Testes de correção e verificação de memória (`make teste`, `make memoria`)", 9.2)
    d.paragrafo(
        "Os 10 testes em `tests/teste_corretude.c` usam `assert()` e distinguem explicitamente **defeitos de implementação** (tolerância zero) "
        "de **erros permitidos pelo método** (falsos positivos controlados próximos de P''):",
        8.4, depois=2)
    d.tabela(["Testes", "Categoria e invariante verificada", "Critério de aceitação e resultado observado"], [
        ["T1 – T3", "Casos-limite (NULL, 0 bits, 0 hashes, filtro vazio, chave `\"\"`)", "Devolve NULL/false sem falha; filtro vazio rejeita em 1 bit com φ''=1,0. **Passou**"],
        ["T4 – T5", "Exemplo manual (64 bits, d=3) e repetição (100× mesma chave)", "Liga 1..d bits nos endereços exatos; repetições não alteram contagem de 1s. **Passou**"],
        ["T6", "Invariante I2 — ausência de falsos negativos (10.000 chaves)", "100% das chaves inseridas retornam `true` (0 falsos negativos). **Passou**"],
        ["T7", "Erro permitido — busca sem sucesso (n=10⁴, P''=1/16, 10⁵ buscas)", "Taxa medida = **0,0612** (dentro da faixa [0,031; 0,125] em torno de 0,0625). **Passou**"],
        ["T8", "Saturação extrema (32 bits recebendo 500 chaves)", "φ'' < 0,05 e falso positivo esperado ocorre, porém I2 mantém 0 falsos negativos. **Passou**"],
        ["T9 – T10", "Fórmulas do artigo (caso n=50 mil, P''=1/16 e ponto ótimo φ''≈0,5)", "Obtido d=4 e N''=288.540 (<300 mil); para n=20 mil, φ'' medido=**0,4977** (teór. 0,5000). **Passou**"],
        ["ASan+UBSan", "Segurança de memória (`-fsanitize=address,undefined`)", "0 acessos inválidos, 0 comportamentos indefinidos, 0 vazamentos de memória. **Passou**"],
    ], [1.2, 4.0, 5.2], 7.3)

    d.subsecao("4.2 Experimento: as equações de Bloom (1970) descrevem o comportamento real em C?", 9.2)
    d.paragrafo(
        "**Protocolo:** Variaram-se **n ∈ {10.000, 100.000, 1.000.000}**, **P'' alvo ∈ {1/2, 1/4, 1/8, 1/16, 1/32, 1/64}** (dimensionados por `filtro_criar_otimo`) "
        "e **duas distribuições de chaves**: sequencial (`i_<rep>_<i>`) e pseudoaleatória hexadecimal (SplitMix64, 16 dígitos). Cada configuração teve **10 repetições** "
        "independentes e determinísticas (semente = índice da repetição, sem `rand()`), inserindo n chaves e consultando **100.000 chaves ausentes** por construção "
        "(referência exata: todo aceite é falso positivo). A geração das chaves foi alocada previamente e ficou fora da cronometragem (`clock_gettime(CLOCK_MONOTONIC)`). "
        "Ambiente: %s | %s | `%s` | %s. Os valores abaixo reportam média ± desvio padrão amostral."
        % (ENV["cpu"], ENV["gcc"].split(" (")[0] + " " + ENV["gcc"].split(" ")[-1], ENV["flags"], ENV["so"]),
        8.2, depois=2.5, entrelinha=1.22)
    linhas = []
    for p in P_VALORES:
        a, b, c = (linha_exp("aleatoria", n, p) for n in (10000, 100000, 1000000))
        linhas.append([frac(p), int(c["d"]), pt(c["bits_por_chave"]), pt(c["phi_emp"], 4),
                       "%s ± %s" % (pt(a["P_emp"], 4), pt(a["P_dp"], 4)),
                       "%s ± %s" % (pt(b["P_emp"], 4), pt(b["P_dp"], 4)),
                       "%s ± %s" % (pt(c["P_emp"], 4), pt(c["P_dp"], 4)),
                       "%s (%s)" % (pt(c["T_emp"], 3), pt(t_exato(c), 3)),
                       "%s ± %s" % (pt(c["ns_inserir"], 0), pt(c["ns_inserir_dp"], 0)),
                       "%s ± %s" % (pt(c["ns_consultar"], 0), pt(c["ns_consultar_dp"], 0))])
    d.tabela(["P'' alvo", "d", "bits/ch.", "φ'' (n=10⁶)", "P'' medido n=10⁴", "P'' medido n=10⁵", "P'' medido n=10⁶", "T'' med. (exato)", "ns/ins. (10⁶)", "ns/cons. (10⁶)"],
             linhas, [0.85, 0.45, 0.85, 1.05, 1.65, 1.65, 1.65, 1.45, 1.2, 1.25], 6.8, ["centro"] * 10)
    d.paragrafo(
        "**Nota sobre as chaves sequenciais:** embora a tabela acima exiba a distribuição pseudoaleatória, todas as 18 combinações também foram executadas com chaves "
        "sequenciais (dados completos em `docs/testes.pdf` e `resultados/experimento.csv`). A comparação entre ambas é analisada na seção seguinte.",
        7.9, depois=2, cor=CINZA)

    # ---- PÁGINA 3: GRÁFICOS + ANÁLISE + HIFENIZAÇÃO + LIMITAÇÕES + CONTRIBUIÇÕES ----
    d.nova_pagina()
    d.subsecao("4.3 Gráficos e interpretação dos resultados", 9.2)
    d.figura(110, lambda ctx, x, y, w, h: (graf_p_emp(ctx, x, y, w / 2 - 4, h, tam=7.0), graf_bits(ctx, x + w / 2 + 4, y, w / 2 - 4, h, tam=7.0)))
    d.legenda("Figura 1 – Esq.: P'' medido × alvo (chaves pseudoaleatórias). Dir.: Bloom usa 1,44–8,66 bits/chave vs 130 do método convencional.", 7.0)
    d.espaco(6)
    d.figura(110, lambda ctx, x, y, w, h: (graf_t(ctx, x, y, w / 2 - 4, h, tam=7.0), graf_tempo(ctx, x + w / 2 + 4, y, w / 2 - 4, h, tam=7.0)))
    d.legenda("Figura 2 – Esq.: T'' medido segue (1−(1−φ'')^d)/φ''. Dir.: tempo por consulta cresce com d e n por efeito de hierarquia de cache.", 7.0)

    s_a = resumo_z("aleatoria")
    s_s = resumo_z("sequencial")
    dp_seq = linha_exp("sequencial", 10000, 0.5)["P_dp"]
    dp_ale = linha_exp("aleatoria", 10000, 0.5)["P_dp"]
    d.lista([
        "**Ponto ótimo (φ''):** em todas as 36 configurações (2 distribuições × 3 tamanhos × 6 erros), φ'' empírico manteve-se em **0,500** (desvio ≤ 0,007), confirmando o dimensionamento.",
        "**Aderência de P'' e efeito da distribuição:** com chaves **pseudoaleatórias**, **%d de %d** configurações ficaram a menos de 2 erros-padrão de (1−φ'')^d (desvio relativo máximo de **%.1f%%**). "
        "Com chaves **sequenciais**, o desvio padrão foi até 4,8× maior (ex.: P''=1/2, n=10⁴: %s vs %s) e **%d/%d** ficaram abaixo de 2 erros-padrão — evidenciando que hashes não criptográficos "
        "(FNV-1a/DJB2) sofrem pequena perda de uniformidade em strings com prefixo comum, embora a média permaneça próxima da teoria."
        % (s_a[0], s_a[2], 100 * maior_desvio_rel("aleatoria"), pt(dp_seq, 4), pt(dp_ale, 4), s_s[0], s_s[2]),
        "**Tempo de rejeição (T''):** o artigo aproxima T'' = 1/φ'' = 2 assumindo d grande; como na prática d ∈ {1…6} é finito e o falso positivo interrompe no d-ésimo bit, a soma truncada "
        "**(1 − (1 − φ'')^d)/φ''** reproduz T'' medido (ex.: 1,000 em d=1; 1,873 vs 1,875 em d=4; 1,969 vs 1,969 em d=6).",
        "**Espaço e tempo de máquina:** o filtro usa de **1,44 a 8,66 bits/chave** (22,5× menos que os 130 bits/chave do método convencional em P''=1/16). "
        "O tempo de consulta (27–95 ns no geral; 54–95 ns nas pseudoaleatórias) sobe de n=10⁵ (≈ 70 KB em P''=1/16, cabe na L2) para n=10⁶ (≈ 704 KB); **tempo medido não comprova complexidade assintótica**.",
    ], 7.8, depois=1.0, entrelinha=1.15)

    d.subsecao("4.4 Reprodução da aplicação do artigo: hifenização com dicionário em disco", 9.0)
    d.paragrafo(
        "Simulação do caso da Seção 7 do artigo (500.000 palavras totais; 50.000 exceções guardadas no filtro em RAM; 450.000 palavras regulares). "
        "Cada aceitação gera 1 acesso simulado ao disco (50.000 reais + falsos positivos).",
        7.9, depois=1.2)
    linhas_hif = []
    for l in HIF:
        a = ARTIGO_TABELA[l["P_alvo"]]
        linhas_hif.append([frac(l["P_alvo"]), int(l["d"]), milhar(l["N_bits"]), milhar(a[0]), milhar(l["falsos_positivos"]),
                           milhar(l["acessos_disco"]), pt(100 * l["economia_acessos"], 1) + "%", pt(a[1], 1) + "%"])
    d.tabela(["P'' alvo", "d", "N'' (nossa imp.)", "N'' (artigo)", "Falsos pos.", "Acessos disco", "Economia (aqui)", "Economia (artigo)"],
             linhas_hif, [0.9, 0.4, 1.35, 1.2, 1.15, 1.3, 1.35, 1.35], 6.8, ["centro"] * 8)
    d.paragrafo(
        "Em P''=1/16, obtivemos **84,4%** de redução de acessos com N''=288.540 bits (< 300.000 bits citados por Bloom). Nosso N'' é levemente menor que o da Tabela I "
        "porque o autor arredondou leituras visuais do seu gráfico normalizado, enquanto aplicamos a fórmula exata do ponto ótimo.",
        7.8, depois=1.5, entrelinha=1.15)

    d.secao("5. Limitações conhecidas", 9.8)
    d.lista([
        "**Estruturais:** não permite remoção de chaves (I1 exige reconstruir o filtro); requer estimativa prévia de n (acima dele P'' cresce rápido); todo aceite exige teste secundário.",
        "**Da implementação e experimento:** hash duplo com FNV-1a/DJB2 (não resistente a adversários); colisões internas de endereços não são impedidas; dicionário em disco apenas simulado; "
        "medições feitas em uma única máquina e sujeitas a variação de cache/escalonamento.",
    ], 7.8, depois=1.0, entrelinha=1.15)

    d.secao("6. Contribuições de cada integrante e declaração de uso de IA", 9.8)
    d.tabela(["Integrante", "Contribuição efetiva no trabalho (preencher antes da entrega final)"],
             [[n, "____________________________________________________________"] for n in INTEGRANTES], [3.2, 6.8], 7.0)
    d.paragrafo(
        "**Declaração de uso de IA:** um assistente de IA foi utilizado, sob solicitação do grupo, como apoio para estruturar, simplificar e comentar o código em C, elaborar os testes "
        "automatizados, estruturar o experimento e redigir/diagramar os documentos em PDF. Todos os programas foram compilados e executados localmente pelo grupo, conferindo a saída dos "
        "testes e a aderência dos resultados às equações do artigo. Todos os integrantes respondem integralmente pelo conteúdo entregue.",
        7.7, depois=1.0, entrelinha=1.15)

    paginas_conteudo = d.pagina
    d.nova_pagina()
    d.secao("Referências bibliográficas", 11)
    d.lista([
        "**[Artigo base]** " + REF_BLOOM + " — Define os três fatores (espaço N, tempo de rejeição T, erro P), compara o método convencional, Método 1 e Método 2 (Filtro de Bloom) e apresenta a aplicação de hifenização (Tabela I).",
        "**[Hash duplo]** Kirsch, A.; Mitzenmacher, M. (2006). Less hashing, same performance: building a better Bloom filter. Proceedings of the 14th European Symposium on Algorithms (ESA 2006), pp. 456–467. — Demonstra que combinar dois hashes independentes preserva assintoticamente o desempenho de d hashes independentes.",
        "**[Hash FNV-1a]** Fowler, G.; Noll, L. C.; Vo, K.-P. The FNV Non-Cryptographic Hash Algorithm (variante FNV-1a de 64 bits). Disponível em: http://www.isthe.com/chongo/tech/comp/fnv/ — Utilizado como `calcular_primeiro_hash_fnv1a` em `src/filtro_bloom.c`.",
        "**[Hash DJB2]** Bernstein, D. J. Hash DJB2. Descrição clássica documentada em: http://www.cse.yorku.ca/~oz/hash.html — Utilizado com etapa adicional de mistura de bits como `calcular_segundo_hash_djb2`.",
        "**[Gerador SplitMix64]** Steele, G. L.; Lea, D.; Flood, C. H. (2014). Fast splittable pseudorandom number generators. OOPSLA 2014, pp. 453–472. — Utilizado em `tests/experimento.c` para gerar chaves pseudoaleatórias determinísticas e reproduzíveis.",
        "**[Aplicação na literatura]** Chang, F. et al. (2006). Bigtable: a distributed storage system for structured data. OSDI 2006, pp. 205–218. — Aplicação de referência citada no seminário para redução de leituras em disco (SSTables).",
        "**[Enunciado]** Universidade Federal da Fronteira Sul (2026). Estudo e implementação de uma solução de artigo científico — Roteiro de avaliação de Estruturas de Dados II (GEX1210), UFFS Campus Chapecó.",
    ], 8.8, depois=5, entrelinha=1.3)
    d.fim()
    return paginas_conteudo


if __name__ == "__main__":
    os.makedirs(DOCS, exist_ok=True)
    quais = sys.argv[1:] or ["relatorio", "testes", "slides"]
    if "relatorio" in quais:
        n = gerar_relatorio()
        print("relatorio.pdf: %d páginas de conteúdo (+ referências)" % n)
    if "testes" in quais:
        import gerar_testes
        gerar_testes.gerar()
        print("testes.pdf gerado")
    if "slides" in quais:
        import gerar_slides
        gerar_slides.gerar()
        print("slides.pdf gerado")
