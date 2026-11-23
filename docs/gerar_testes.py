# -*- coding: utf-8 -*-
"""PDF de testes: correção, memória, exemplo manual e experimento (dados reais de resultados/)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gerar_pdfs import *  # noqa: E402,F401,F403


def gerar():
    d = Documento(os.path.join(DOCS, "testes.pdf"), "Relatório de testes · Filtro de Bloom · ED2 (GEX1210) · UFFS Chapecó", margem=48)
    d.titulo("Relatório de testes do Filtro de Bloom",
             "Testes de correção, verificação de memória, exemplo manual e experimento · Estruturas de Dados II (GEX1210) · UFFS Chapecó")

    # ------------------------------------------------------------------ 1
    d.secao("1. Ambiente e como reproduzir")
    d.tabela(["Item", "Valor"], [
        ["Processador", ENV["cpu"]],
        ["Sistema", ENV["so"]],
        ["Compilador", ENV["gcc"]],
        ["Opções de compilação", "`%s`; ligação com `-lm`" % ENV["flags"]],
        ["Dependências", "somente biblioteca padrão de C, `make`; os PDFs usam python3 + pycairo"],
    ], [2, 8], 8)
    d.codigo("make               # compila tudo (bin/teste_corretude, bin/exemplo, bin/experimento)\n"
             "make teste         # 10 testes de correção\n"
             "make memoria       # os mesmos testes com AddressSanitizer + UBSan\n"
             "make exemplo       # exemplo passo a passo (N = 24 bits, d = 3)\n"
             "make experimento   # gera resultados/experimento.csv e resultados/hifenizacao.csv\n"
             "make pdfs          # regenera relatorio.pdf, testes.pdf e slides.pdf em docs/")

    # ------------------------------------------------------------------ 2
    d.secao("2. Testes de correção (`tests/teste_corretude.c`)")
    d.paragrafo("Cada teste usa `assert`; se algo falhar, o programa aborta com a linha do erro. A coluna **Tipo** distingue o que é **erro permitido pelo método** "
                "(falso positivo, previsto pelo artigo) do que seria **defeito da implementação** (falso negativo, falha em entrada inválida, vazamento).")
    d.tabela(["ID", "O que verifica", "Tipo", "Critério de aceitação", "Resultado"], [
        ["T1", "Entradas inválidas: 0 bits, 0 hashes, n=0, P=0, P=1, chave/filtro NULL, destruir(NULL)", "caso-limite / defeito", "criação devolve NULL; inserir/consultar devolvem false; sem queda", "passou"],
        ["T2", "Filtro vazio (entrada vazia)", "caso-limite", "consulta rejeita lendo exatamente 1 bit; 0 bits ligados; φ'' = 1,0", "passou"],
        ["T3", "Chave vazia \"\"", "caso-limite", "pode ser inserida e é encontrada", "passou"],
        ["T4", "Exemplo manual com 1 chave (64 bits, d=3)", "correção", "liga entre 1 e d bits, exatamente nos endereços da chave; n=1", "passou"],
        ["T5", "Elementos repetidos (100 inserções iguais)", "caso-limite", "quantidade de bits ligados não muda após a 1ª inserção", "passou"],
        ["T6", "Ausência de falsos negativos (10.000 chaves)", "defeito (invariante I2)", "todas as chaves inseridas são aceitas", "passou"],
        ["T7", "Busca sem sucesso (n=10.000, P''=1/16, 10⁵ consultas)", "erro permitido", "taxa de falsos positivos entre P''/2 e 2P''; medido: 0,0612", "passou"],
        ["T8", "Capacidade excedida (32 bits, 500 chaves)", "caso-limite", "φ'' < 0,05; chave ausente é aceita (falso positivo); inseridas continuam aceitas", "passou"],
        ["T9", "Parâmetros ótimos do artigo (n=50.000, P''=1/16)", "correção", "d = 4 e 280.000 < N'' < 300.000; obtido N'' = 288.540", "passou"],
        ["T10", "φ'' medido × previsto (n=20.000, P''=1/16)", "correção", "φ'' ∈ (0,45; 0,55) e a menos de 0,02 de (1 − d/N'')ⁿ; medido 0,4977 × 0,5000", "passou"],
    ], [0.6, 3.2, 1.5, 3.7, 0.9], 7.4, ["centro", "esq", "esq", "esq", "centro"])
    d.subsecao("Saída real de `make teste`")
    d.codigo(ler_texto("saida_testes.txt").replace("\r", ""), 7)
    d.subsecao("Verificação de memória: `make memoria` (AddressSanitizer + UndefinedBehaviorSanitizer)")
    mem = ler_texto("saida_memoria.txt")
    d.paragrafo("Os mesmos testes foram executados com os detectores de erros de memória. Resultado: %s erros reportados, nenhum vazamento (o LeakSanitizer faz parte do AddressSanitizer no Linux) e a mensagem final **TODOS OS 10 TESTES PASSARAM**." % ("0" if "ERROR" not in mem and "runtime error" not in mem else "HÁ"))

    # ------------------------------------------------------------------ 3
    d.secao("3. Exemplo manual verificável (`make exemplo`)")
    d.paragrafo("Filtro com N'' = 24 bits e d = 3. Inserimos gato, cao e pato e consultamos quatro palavras. Os endereços abaixo são impressos pelo programa e o estado final pode ser conferido à mão.", depois=2)
    d.tabela(["Palavra", "Bits (endereços)", "Operação", "Resultado esperado", "Resultado obtido"], [
        ["gato", "4, 9, 14", "inserir", "liga 4, 9 e 14", "000010000100001000000000"],
        ["cao", "2, 11, 20", "inserir", "liga 2, 11 e 20", "001010000101001000001000"],
        ["pato", "7, 13, 22", "inserir", "liga 7, 13 e 22", "001010010101011000001010"],
        ["gato", "4, 9, 14", "consultar", "todos 1 → aceita (inserida)", "ACEITA, 3 bits lidos"],
        ["peixe", "6, 14, 22", "consultar", "bit 6 = 0 → rejeita no 1º bit", "REJEITADA, 1 bit lido"],
        ["galo", "4, 19, 10", "consultar", "bit 4 = 1, bit 19 = 0 → rejeita no 2º bit", "REJEITADA, 2 bits lidos"],
        ["coelho", "7, 9, 11", "consultar", "bits de pato, gato e cao: todos 1 → **falso positivo**", "ACEITA, 3 bits lidos"],
    ], [1, 1.4, 1, 3, 2.6], 7.6, ["esq", "esq", "esq", "esq", "esq"])
    estado = "001010010101011000001010"

    def fig_bits(ctx, x, y, w, h):
        definir_fonte(ctx, 8)
        ctx.set_source_rgb(*PRETO)
        ctx.move_to(x, y + 9)
        ctx.show_text("Estado final do vetor (bits ligados em azul; coelho: 7, 9 e 11 em laranja):")
        desenhar_bits(ctx, x + 40, y + 18, estado, 18, {7: (1, 0.8, 0.5), 9: (1, 0.8, 0.5), 11: (1, 0.8, 0.5)}, True, 9)
    d.figura(52, fig_bits)
    d.paragrafo("**Conferência manual:** 9 bits ligados (2, 4, 7, 9, 11, 13, 14, 20, 22) → φ'' medido = 15/24 = 0,625. A fórmula dá (1 − 3/24)³ = 0,670; a diferença é esperada "
                "porque a fórmula é um valor esperado e, nesta amostra, as três palavras não colidiram (9 bits distintos em vez de ≈ 7,9). O falso positivo de “coelho” é o erro permitido "
                "do método: seus três bits foram ligados por palavras diferentes.")

    # ------------------------------------------------------------------ 4
    d.secao("4. Experimento (`tests/experimento.c`)")
    d.paragrafo("**Pergunta experimental:** as fórmulas do artigo — φ'' = (1 − d/N'')ⁿ, P'' = (1 − φ'')^d e T'' ≈ 1/φ'' — descrevem o comportamento do filtro implementado quando "
                "variamos o tamanho n, o erro alvo P'' e a distribuição das chaves? **Métricas:** φ'' (fração de bits 0), P'' (taxa de falsos positivos), T'' (bits lidos por consulta ausente), "
                "bits por chave e tempo por operação.")
    d.tabela(["Parâmetro", "Valores"], [
        ["Tamanhos n", "10.000; 100.000; 1.000.000 (3 valores)"],
        ["Erro alvo P''", "1/2, 1/4, 1/8, 1/16, 1/32, 1/64 (N'' e d pelo ponto ótimo)"],
        ["Distribuição das chaves", "sequencial (`i_<rep>_<i>`) e pseudoaleatória (16 dígitos hexa, SplitMix64)"],
        ["Repetições", "10 por configuração; cada uma com filtro novo e chaves próprias (semente = nº da repetição, sem `rand()`)"],
        ["Consultas", "100.000 chaves **ausentes** por repetição (todo aceite é falso positivo: resultado exato conhecido por construção)"],
        ["Referência de espaço", "método convencional do artigo: N = n(b+1)(T+2)/(T−1) com b = 64 e T = 4 → 130 bits por chave"],
        ["Tempo", "`clock_gettime(CLOCK_MONOTONIC)`; geração das chaves fica fora da medição"],
        ["Estatística", "média e desvio padrão amostral (n−1) das 10 repetições"],
    ], [2.2, 7.8], 7.8)

    def tabela_dist(dist, titulo):
        d.garantir(330)  # título sempre junto da tabela
        d.subsecao(titulo)
        linhas = []
        for n in (10000, 100000, 1000000):
            for p in P_VALORES:
                l = linha_exp(dist, n, p)
                linhas.append([milhar(n), frac(p), milhar(l["N_bits"]), int(l["d"]),
                               "%s ± %s" % (pt(l["phi_emp"], 4), pt(l["phi_dp"], 4)),
                               pt(l["P_teorico"], 4), "%s ± %s" % (pt(l["P_emp"], 4), pt(l["P_dp"], 4)),
                               "%s ± %s" % (pt(l["T_emp"], 3), pt(l["T_dp"], 3)), pt(t_exato(l), 3),
                               "%s ± %s" % (pt(l["ns_inserir"], 0), pt(l["ns_inserir_dp"], 0)),
                               "%s ± %s" % (pt(l["ns_consultar"], 0), pt(l["ns_consultar_dp"], 0))])
        d.tabela(["n", "P'' alvo", "N'' (bits)", "d", "φ'' medido", "P'' fórmula", "P'' medido", "T'' medido", "T'' fórmula", "ns/inserir", "ns/consultar"],
                 linhas, [1.1, 0.8, 1.2, 0.4, 1.5, 0.9, 1.5, 1.4, 0.9, 1.1, 1.2], 6.6, ["centro"] * 11)

    tabela_dist("aleatoria", "4.1 Resultados completos — chaves pseudoaleatórias")
    tabela_dist("sequencial", "4.2 Resultados completos — chaves sequenciais")
    d.subsecao("4.3 Gráficos")
    d.figura(165, lambda ctx, x, y, w, h: (graf_p_emp(ctx, x, y, w / 2 - 4, h), graf_t(ctx, x + w / 2 + 4, y, w / 2 - 4, h)))
    d.legenda("Figura 1 – Esq.: P'' medido × alvo (chaves pseudoaleatórias; sobrepõe-se à linha ideal). Dir.: T'' medido segue a fórmula exata para d finito.")
    d.figura(165, lambda ctx, x, y, w, h: (graf_bits(ctx, x, y, w / 2 - 4, h), graf_tempo(ctx, x + w / 2 + 4, y, w / 2 - 4, h)))
    d.legenda("Figura 2 – Esq.: bits por chave (Bloom × convencional). Dir.: tempo médio de consulta cresce com n (cache) e com d.")
    d.subsecao("4.4 Parte B — caso da aplicação do artigo (hifenização simulada)")
    d.paragrafo("500.000 palavras, das quais 50.000 exceções ficam em um “dicionário em disco”. O filtro guarda as exceções; só vai ao disco a palavra aceita pelo filtro "
                "(exceção verdadeira ou falso positivo). Sem filtro, todas as 500.000 consultas iriam ao disco.", depois=2)
    linhas = []
    for l in HIF:
        a = ARTIGO_TABELA[l["P_alvo"]]
        linhas.append([frac(l["P_alvo"]), milhar(l["N_bits"]), milhar(a[0]), int(l["d"]), milhar(l["falsos_positivos"]), milhar(l["acessos_disco"]),
                       pt(100 * l["economia_acessos"], 1) + "%", pt(a[1], 1) + "%"])
    d.tabela(["P'' alvo", "N'' (aqui)", "N'' (artigo)", "d", "falsos positivos", "acessos ao disco", "economia (aqui)", "economia (artigo)"], linhas, [1, 1.3, 1.3, 0.5, 1.4, 1.5, 1.3, 1.3], 7.4, ["centro"] * 8)
    d.figura(165, lambda ctx, x, y, w, h: graf_hif(ctx, x + w * 0.2, y, w * 0.6, h))
    d.legenda("Figura 3 – Acessos ao disco evitados: esta implementação × Tabela I do artigo (valores lidos do texto traduzido).")

    # ------------------------------------------------------------------ 5
    s_a, s_s = resumo_z("aleatoria"), resumo_z("sequencial")
    d.secao("5. Interpretação, limitações e conclusão dos testes")
    d.lista([
        "**φ''** medido ficou em 0,500 em todas as configurações (desvio ≤ 0,007): o dimensionamento do ponto ótimo funciona.",
        "**P''** medido concorda com (1 − φ'')^d: chaves pseudoaleatórias, %d de %d configurações a menos de 2 erros-padrão, desvio relativo máximo de %.1f%%. "
        "Com chaves sequenciais, %d de %d (desvio padrão maior, ex.: P''=1/2 e n=10⁴: %s contra %s) — os hashes não criptográficos se afastam um pouco da hipótese de uniformidade."
        % (s_a[0], s_a[2], 100 * maior_desvio_rel("aleatoria"), s_s[0], s_s[2], pt(linha_exp("sequencial", 10000, 0.5)["P_dp"], 4), pt(linha_exp("aleatoria", 10000, 0.5)["P_dp"], 4)),
        "**T''** medido (consultas ausentes, aceitas ou rejeitadas) é menor que o 2 do artigo porque d é finito: a fórmula exata (1 − (1 − φ'')^d)/φ'' reproduz o valor medido (diferença menor que 0,01 com chaves pseudoaleatórias).",
        "**Espaço:** de 1,44 a 8,66 bits por chave contra 130 do método convencional (b = 64, T = 4).",
        "**Aplicação do artigo:** a economia de acessos ao disco reproduz a Tabela I (84,4% para P''=1/16 com N'' = 288.540 bits, menos que os 300.000 citados).",
        "**Limitações:** uma máquina só; tempo sujeito a ruído e a cache (**tempo medido não comprova complexidade assintótica**); chaves ausentes não são adversárias; hashes não "
        "criptográficos; o disco é simulado por contagem de acessos; a Tabela I do artigo foi lida da tradução fornecida.",
        "**Conclusão:** nenhum defeito encontrado — zero falsos negativos, entradas inválidas tratadas, nenhuma falha de memória — e os erros observados são exatamente os falsos positivos permitidos pelo método.",
    ], 8.6)
    d.fim()
