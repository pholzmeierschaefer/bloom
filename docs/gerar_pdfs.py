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
            "P'' alvo", "bits lidos por consulta", (0.012, 0.65), (0.8, 2.2), P_VALORES, [1, 1.25, 1.5, 1.75, 2],
            True, False, rotulo_p, lambda v: pt(v, 2), titulo="Tempo de rejeição T'' (n = 10⁶)", tam=tam)


def graf_tempo(ctx, x, y, w, h, tam=7.5):
    series = []
    cores = {0.5: ROXO, 0.0625: AZUL, 0.015625: VERMELHO}
    for p, cor in cores.items():
        pts = [(n, linha_exp("aleatoria", n, p)["ns_consultar"]) for n in (10000, 100000, 1000000)]
        series.append({"label": "P''=%s (d=%d)" % (frac(p), int(linha_exp("aleatoria", 10000, p)["d"])), "cor": cor, "pontos": pts})
    grafico(ctx, x, y, w, h, series, "n (chaves inseridas)", "ns por consulta (média)", (7000, 1.5e6), (0, 100),
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
# 1) RELATÓRIO
# ---------------------------------------------------------------------------
def gerar_relatorio():
    d = Documento(os.path.join(DOCS, "relatorio.pdf"), "Relatório técnico · Filtro de Bloom · ED2 (GEX1210) · UFFS Chapecó", margem=48)
    d.titulo("Filtro de Bloom (Método 2 de Bloom, 1970): solução, implementação em C e avaliação",
             "Estruturas de Dados II (GEX1210) · UFFS Campus Chapecó · Relatório técnico · Novembro de 2026")
    d.paragrafo("**Integrantes:** " + "; ".join(n + " (matrícula: ____)" for n in INTEGRANTES) + ".", 8.6)
    d.paragrafo("**Artigo:** " + REF_BLOOM, 8.6)

    d.secao("1. Problema e escopo implementado")
    d.paragrafo("Dado um conjunto de n mensagens, responder “esta mensagem pertence ao conjunto?” usando pouco espaço, quando quase todas as "
                "consultas são de mensagens **ausentes**. Bloom troca certeza por espaço: aceita uma fração permitida P'' de **falsos positivos** "
                "(erro de comissão) e garante **zero falsos negativos**. Os três fatores do artigo são o espaço N'' (bits), o tempo de rejeição T'' "
                "(bits examinados até concluir que a mensagem está ausente) e o erro permitido P''.")
    d.lista([
        "**Implementado (núcleo em src/filtro_bloom.c):** `filtro_criar`, `filtro_criar_otimo`, `filtro_inserir`, `filtro_consultar`, `filtro_destruir` e as "
        "medidas φ'' (medido e previsto) e P'' (previsto). Chaves são textos terminados em `'\\0'`.",
        "**Simplificações (identificadas):** (i) os d endereços saem de **hash duplo** — FNV-1a e DJB2 com mistura final — como h1 + i·passo mod N'', em vez de d "
        "funções independentes; (ii) os d endereços de uma chave podem coincidir; (iii) o dicionário em disco da aplicação de hifenização é **simulado**: "
        "contamos como “acessos ao disco” as consultas aceitas; (iv) o Método 1 do artigo aparece só pelas fórmulas, não foi implementado.",
        "**Fora do escopo:** remoção de chaves, redimensionamento, persistência, hashes criptográficos.",
    ])

    d.secao("2. Solução, invariantes e correspondência com o artigo")
    d.paragrafo("A estrutura é um vetor de N'' bits, inicialmente todos 0. **Inserir** a mensagem x liga os d bits de endereços a₁…a_d de x. **Consultar** x lê esses d bits: "
                "se algum vale 0, x é **rejeitada** (certamente ausente); se todos valem 1, x é **aceita** (provavelmente presente).")
    d.tabela(["Artigo", "Código", "Significado"], [
        ["N''", "`total_bits`", "bits do vetor"],
        ["d", "`qtd_hashes`", "endereços (bits) por mensagem"],
        ["n", "`qtd_inseridos`", "mensagens inseridas"],
        ["φ'' = (1 − d/N'')ⁿ ≈ e^(−nd/N'')", "`filtro_phi_empirico/teorico`", "fração de bits que valem 0"],
        ["P'' = (1 − φ'')^d", "`filtro_erro_teorico`", "probabilidade de falso positivo"],
        ["T'' ≈ 1/φ''", "argumento `bits_lidos`", "bits lidos até rejeitar"],
        ["Ponto ótimo φ'' = 1/2", "`filtro_criar_otimo`", "d = ⌈log₂(1/P'')⌉; N'' = ⌈n·log₂(1/P'')·log₂e⌉ ≈ 1,44·n·log₂(1/P'')"],
    ], [3.2, 2.6, 4.2], 7.8)
    d.paragrafo("**Invariantes.** **I1:** um bit 1 nunca volta a 0 (não há remoção). **I2:** após inserir x, os d bits de x valem 1; logo **não existem falsos negativos**. "
                "**I3:** se um dos d bits de x vale 0, x nunca foi inserido (rejeição é certa); a aceitação é só provável. Os testes automatizados verificam I2 e I3 diretamente.")

    d.secao("3. Complexidade das operações (parâmetros e hipóteses)")
    d.paragrafo("Sejam |k| o tamanho da chave em caracteres, n o número de chaves, P'' o erro alvo e d = ⌈log₂(1/P'')⌉ (constante para P'' fixo, **independente de n**).", depois=2)
    d.tabela(["Operação", "Custo", "Observação"], [
        ["`filtro_criar`", "O(N''/8) = O(n·log(1/P''))", "`calloc` zera os bytes; espaço N'' bits"],
        ["`filtro_inserir`", "O(|k| + d)", "dois hashes percorrem a chave; d escritas de bit"],
        ["`filtro_consultar`", "pior caso O(|k| + d); rejeição esperada ≈ 1/φ'' = 2 bits lidos", "para no primeiro bit 0 (invariante I3)"],
        ["`filtro_phi_empirico`", "O(N'')", "só medição; não faz parte do uso normal"],
        ["Espaço", "≈ 1,44·n·log₂(1/P'') bits", "convencional: n·(b+1)·(T+2)/(T−1) bits (artigo)"],
    ], [2.2, 4.3, 4.2], 7.8)
    d.paragrafo("**Hipóteses:** as funções de hash se comportam como uniformes e independentes; as mensagens consultadas ausentes se comportam como chaves "
                "aleatórias; o filtro foi dimensionado para o n real (com n maior que o projetado, φ'' cai e P'' sobe — teste T8); |k| é limitado; "
                "acessos à memória têm custo constante (efeitos de cache não entram na fórmula).")

    d.secao("4. Testes e experimento")
    d.subsecao("4.1 Correção (`make teste`, `make memoria`)")
    d.paragrafo("São 10 testes automatizados com `assert`: entradas inválidas (NULL e parâmetros 0), filtro vazio (rejeita lendo 1 bit, φ''=1), chave vazia, exemplo manual, "
                "elementos repetidos (vetor não muda), **ausência de falsos negativos** (10.000 chaves), busca sem sucesso (falsos positivos ≈ P''), saturação (32 bits com 500 chaves), "
                "parâmetros ótimos do artigo (n=50.000, P''=1/16 → d=4, N''=288.540 bits) e φ'' medido ≈ φ'' previsto ≈ 0,5. **Erros permitidos × defeitos:** falso positivo é erro "
                "permitido (o teste só exige taxa entre P''/2 e 2P''); falso negativo, falha em entrada inválida e vazamento de memória são defeitos (exigem zero). Todos passam; "
                "com AddressSanitizer e UBSan não há erros nem vazamentos.")
    d.subsecao("4.2 Experimento: as fórmulas do artigo descrevem o filtro implementado?")
    d.paragrafo("**Método.** n ∈ {10⁴, 10⁵, 10⁶}; P'' alvo ∈ {1/2, …, 1/64} (N'' e d pelo ponto ótimo); duas distribuições de chaves (sequencial `i_3_17` e pseudoaleatória hexadecimal, SplitMix64); "
                "**10 repetições** por configuração, cada uma com filtro novo, n inserções e 10⁵ consultas de chaves ausentes. As chaves são determinísticas (semente = número da repetição, "
                "sem `rand()`); como as consultadas são ausentes por construção, todo aceite é falso positivo (**resultado exato de referência**). A geração das chaves fica fora do tempo medido "
                "(`CLOCK_MONOTONIC`). Ambiente: %s, %s, `%s`, %s. Valores: média ± desvio padrão amostral." % (ENV["cpu"], ENV["gcc"].split(" (")[0] + " " + ENV["gcc"].split(" ")[-1], ENV["flags"], ENV["so"]))
    linhas = []
    for p in P_VALORES:
        a, b, c = (linha_exp("aleatoria", n, p) for n in (10000, 100000, 1000000))
        linhas.append([frac(p), int(c["d"]), pt(c["bits_por_chave"]), pt(c["phi_emp"], 3),
                       "%s ± %s" % (pt(a["P_emp"], 4), pt(a["P_dp"], 4)),
                       "%s ± %s" % (pt(b["P_emp"], 4), pt(b["P_dp"], 4)),
                       "%s ± %s" % (pt(c["P_emp"], 4), pt(c["P_dp"], 4)),
                       "%s (%s)" % (pt(c["T_emp"], 3), pt(t_exato(c), 3)),
                       pt(c["ns_consultar"], 0)])
    d.tabela(["P'' alvo", "d", "bits/chave", "φ'' (n=10⁶)", "P'' medido n=10⁴", "P'' medido n=10⁵", "P'' medido n=10⁶", "T'' medido (fórmula)", "ns/cons."],
             linhas, [1, 0.6, 1, 1.1, 1.9, 1.9, 1.9, 1.7, 1.1], 7.2, ["centro"] * 9)
    d.figura(150, lambda ctx, x, y, w, h: (graf_p_emp(ctx, x, y, w / 2 - 4, h), graf_bits(ctx, x + w / 2 + 4, y, w / 2 - 4, h)))
    d.legenda("Figura 1 – Esq.: erro medido coincide com o alvo (linha tracejada). Dir.: o filtro usa 1,4 a 8,7 bits por chave contra 130 do método convencional.")
    s_a = resumo_z("aleatoria")
    s_s = resumo_z("sequencial")
    dp_seq = linha_exp("sequencial", 10000, 0.5)["P_dp"]
    dp_ale = linha_exp("aleatoria", 10000, 0.5)["P_dp"]
    d.paragrafo("**Resultados e interpretação.** (1) φ'' medido = 0,500 em todas as configurações, como prevê o ponto ótimo. (2) P'' medido acompanha (1−φ'')^d: com chaves pseudoaleatórias, "
                "%d das %d configurações ficam a menos de 2 erros-padrão da fórmula (máx. %.1f%% de desvio relativo) — o artigo descreve bem a implementação. (3) Com chaves **sequenciais** o "
                "desvio padrão é maior (P''=1/2, n=10⁴: %s contra %s) e %d/%d configurações ficam a menos de 2 erros-padrão: os hashes não criptográficos se afastam um pouco da hipótese de "
                "uniformidade nesses dados. (4) T'' medido é menor que o 2 do artigo porque d é finito e a consulta para em d bits: (1−(1−φ'')^d)/φ'' prevê o valor medido (entre parênteses). "
                "(5) O tempo por consulta (entre 27 e 95 ns) cresce com d e com n, o que é efeito de acessos à memória/cache; **tempo medido não comprova complexidade assintótica**. "
                "(6) Espaço: 1,44·log₂(1/P'') bits/chave — para P''=1/16, 5,77 bits contra 130 do método convencional (b = 64 e T = 4), 22 vezes menos."
                % (s_a[0], s_a[2], 100 * maior_desvio_rel("aleatoria"), pt(dp_seq, 4), pt(dp_ale, 4), s_s[0], s_s[2]))
    linhas = []
    for l in HIF:
        a = ARTIGO_TABELA[l["P_alvo"]]
        linhas.append([frac(l["P_alvo"]), milhar(l["N_bits"]), milhar(a[0]), milhar(l["acessos_disco"]), pt(100 * l["economia_acessos"], 1) + "%", pt(a[1], 1) + "%"])
    d.paragrafo("**Caso da aplicação do artigo (hifenização simulada):** 500.000 palavras, 50.000 exceções no dicionário em disco; acessos = exceções + falsos positivos.", depois=2)
    d.tabela(["P'' alvo", "N'' (aqui)", "N'' (artigo)", "acessos ao disco (aqui)", "economia (aqui)", "economia (artigo)"], linhas, [1, 1.3, 1.3, 1.8, 1.4, 1.4], 7.4, ["centro"] * 6)
    d.paragrafo("A economia de acessos coincide com a Tabela I do artigo (84,4% para P''=1/16 com N''=288.540 < 300.000 bits). Nosso N'' é um pouco menor que o do artigo porque usamos a fórmula do ponto "
                "ótimo (1,44·n·log₂(1/P'')) em vez das leituras do gráfico do autor.")
    d.paragrafo("**Limitações do experimento:** uma única máquina; tempo sujeito a ruído; consultas ausentes não são adversárias; apenas hashes não criptográficos; o dicionário em disco é simulado.")

    d.secao("5. Limitações conhecidas")
    d.lista([
        "Não há remoção (I1): retirar uma chave exigiria reconstruir o filtro; n precisa ser estimado antes (acima dele, P'' aumenta).",
        "O falso positivo não some: toda aplicação precisa de um teste secundário para as chaves aceitas.",
        "Hash duplo no lugar de d hashes independentes; hashes FNV-1a/DJB2 não resistem a um adversário; endereços de uma chave podem coincidir.",
        "O Método 1 do artigo não foi implementado; a aplicação em navegadores (slides) é uma hipótese fundamentada, não um sistema construído.",
    ])

    d.secao("6. Contribuições de cada integrante e uso de IA")
    d.tabela(["Integrante", "Contribuição (registrar o que cada um fez)"], [[n, "______________________________"] for n in INTEGRANTES], [3, 7], 7.8)
    d.paragrafo("**Uso de IA:** um assistente de IA foi usado, a pedido do grupo, para redigir e simplificar o código em C, os testes, o experimento e o texto destes PDFs. Os testes e o experimento foram "
                "executados e os resultados conferidos contra as fórmulas do artigo. Todo integrante deve conseguir explicar o material entregue.", 8.6)
    paginas_conteudo = d.pagina
    d.nova_pagina()
    d.secao("Referências")
    d.lista([
        REF_BLOOM,
        "Fowler, G.; Noll, L. C.; Vo, K.-P. FNV hash (variante FNV-1a de 64 bits). http://www.isthe.com/chongo/tech/comp/fnv/",
        "Bernstein, D. J. Hash DJB2. Descrição em http://www.cse.yorku.ca/~oz/hash.html",
        "Steele, G. L.; Lea, D.; Flood, C. H. (2014). Fast splittable pseudorandom number generators. OOPSLA 2014 (mistura SplitMix64 usada para gerar chaves).",
        "Kirsch, A.; Mitzenmacher, M. (2006). Less hashing, same performance: building a better Bloom filter. ESA 2006 (justifica o hash duplo).",
        "Universidade Federal da Fronteira Sul (2026). Estudo e implementação de uma solução de artigo científico — enunciado do trabalho de ED2 (GEX1210).",
    ], 8.8)
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
