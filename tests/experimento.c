/*
 * ============================================================================
 * MÓDULO DE EXPERIMENTO CIENTÍFICO: tests/experimento.c
 * ============================================================================
 *
 * O que este módulo faz:
 *   Executa o experimento empírico exigido pelo trabalho para verificar se as
 *   fórmulas matemáticas do artigo de Bloom (1970) descrevem o comportamento
 *   real da nossa implementação em C.
 *
 * O experimento é dividido em duas partes:
 *   - Parte A (executar_experimento_principal):
 *       Varia a quantidade de elementos n (10.000, 100.000 e 1.000.000), a taxa
 *       de erro alvo P'' (1/2 até 1/64) e a distribuição das chaves (sequencial
 *       e pseudoaleatória). Para cada caso, executa 10 repetições, calcula média
 *       e desvio padrão de phi'', P'', T'' e tempo por operação, e salva em
 *       resultados/experimento.csv.
 *   - Parte B (simular_caso_hifenizacao):
 *       Reproduz o exemplo numérico da Tabela I do artigo (500.000 palavras,
 *       onde 50.000 são exceções guardadas num dicionário em disco) e mede a
 *       porcentagem real de acessos a disco economizados, salvando em
 *       resultados/hifenizacao.csv.
 *
 * Reprodutibilidade:
 *   As chaves são geradas de forma determinística a partir do número da
 *   repetição (sem rand()), e a preparação das chaves fica fora do tempo medido.
 * ============================================================================
 */

#include "filtro_bloom.h" /* Interface do Filtro de Bloom */
#include <math.h>         /* Função sqrt para o desvio padrão */
#include <stdio.h>        /* Funções printf, snprintf, fopen, fprintf e fclose */
#include <stdlib.h>       /* Funções malloc, free e exit */
#include <time.h>         /* Função clock_gettime e struct timespec */

#define QUANTIDADE_REPETICOES 10         /* Quantas vezes cada configuração é repetida */
#define QUANTIDADE_CONSULTAS_AUSENTES 100000 /* Quantas chaves ausentes são testadas por repetição */
#define TAMANHO_MAXIMO_CHAVE 24          /* Tamanho do buffer em bytes reservado para cada chave */
#define BITS_POR_MENSAGEM_CONVENCIONAL 64 /* Tamanho b usado na comparação com tabela hash convencional */

/*
 * Calcula a média aritmética e o desvio padrão amostral (divisão por quantidade - 1)
 * de um vetor de resultados numéricos.
 */
static void calcular_media_e_desvio(const double *valores,
                                    int quantidade,
                                    double *media_saida,
                                    double *desvio_padrao_saida) {
    double soma = 0.0;
    for (int indice = 0; indice < quantidade; indice++) {
        soma += valores[indice];
    }
    *media_saida = soma / quantidade;

    double soma_diferencas_ao_quadrado = 0.0;
    for (int indice = 0; indice < quantidade; indice++) {
        double diferenca = valores[indice] - *media_saida;
        soma_diferencas_ao_quadrado += diferenca * diferenca;
    }
    *desvio_padrao_saida = sqrt(soma_diferencas_ao_quadrado / (quantidade - 1));
}

/*
 * Lê o relógio monotônico do sistema operacional e devolve o instante atual em nanossegundos.
 */
static double obter_tempo_em_nanossegundos(void) {
    struct timespec tempo_atual;
    clock_gettime(CLOCK_MONOTONIC, &tempo_atual);
    return (double)tempo_atual.tv_sec * 1e9 + (double)tempo_atual.tv_nsec;
}

/*
 * Algoritmo SplitMix64: embaralha um número inteiro de 64 bits de forma determinística.
 * Usado para gerar chaves hexadecimais com aparência aleatória mantendo 100% de reprodutibilidade.
 */
static uint64_t embaralhar_bits_64(uint64_t semente) {
    semente += 0x9e3779b97f4a7c15ULL;
    semente = (semente ^ (semente >> 30)) * 0xbf58476d1ce4e5b9ULL;
    semente = (semente ^ (semente >> 27)) * 0x94d049bb133111ebULL;
    return semente ^ (semente >> 31);
}

/*
 * Gera uma chave de texto única para o experimento.
 *   - tipo_distribuicao == 0: gera texto sequencial legível (ex.: "i_0_15" ou "a_0_15").
 *   - tipo_distribuicao == 1: gera texto hexadecimal de 16 dígitos via SplitMix64.
 *   - grupo == 0 representa chaves inseridas; grupo == 1 representa chaves ausentes.
 */
static void gerar_chave_teste(char *destino,
                              int tipo_distribuicao,
                              int numero_repeticao,
                              int grupo,
                              size_t indice) {
    if (tipo_distribuicao == 0) {
        char prefixo = (grupo == 0) ? 'i' : 'a';
        snprintf(destino, TAMANHO_MAXIMO_CHAVE, "%c_%d_%zu", prefixo, numero_repeticao, indice);
    } else {
        uint64_t entrada_mistura = indice + ((uint64_t)(numero_repeticao * 2 + grupo) << 40);
        snprintf(destino, TAMANHO_MAXIMO_CHAVE, "%016llx", (unsigned long long)embaralhar_bits_64(entrada_mistura));
    }
}

/*
 * Parte A: testa todas as combinações de distribuição, tamanho n e erro alvo P''.
 */
static void executar_experimento_principal(void) {
    const size_t tamanhos_entrada[] = {10000, 100000, 1000000};
    const double taxas_erro_alvo[] = {1.0 / 2, 1.0 / 4, 1.0 / 8, 1.0 / 16, 1.0 / 32, 1.0 / 64};
    const char *nomes_distribuicoes[] = {"sequencial", "aleatoria"};

    FILE *arquivo_csv = fopen("resultados/experimento.csv", "w");
    if (arquivo_csv == NULL) {
        perror("resultados/experimento.csv");
        exit(1);
    }

    fprintf(arquivo_csv,
            "distribuicao;n;P_alvo;N_bits;d;bits_por_chave;bits_por_chave_convencional;"
            "phi_teorico;phi_emp;phi_dp;P_teorico;P_emp;P_dp;T_teorico;T_emp;T_dp;"
            "ns_inserir;ns_inserir_dp;ns_consultar;ns_consultar_dp\n");

    printf("%-10s %8s %7s %9s %2s | %6s %6s | %8s %8s | %6s %6s | %8s\n",
           "dist", "n", "P alvo", "N bits", "d", "phi_t", "phi_e", "P_teor", "P_emp", "T_teo", "T_emp", "ns/cons");

    for (int tipo_distribuicao = 0; tipo_distribuicao < 2; tipo_distribuicao++) {
        for (int indice_tamanho = 0; indice_tamanho < 3; indice_tamanho++) {
            size_t quantidade_elementos = tamanhos_entrada[indice_tamanho];

            /* Aloca antecipadamente os vetores de chaves para não incluir malloc no tempo medido */
            char (*chaves_inseridas)[TAMANHO_MAXIMO_CHAVE] = malloc(quantidade_elementos * TAMANHO_MAXIMO_CHAVE);
            char (*chaves_ausentes)[TAMANHO_MAXIMO_CHAVE] = malloc(QUANTIDADE_CONSULTAS_AUSENTES * TAMANHO_MAXIMO_CHAVE);

            for (int indice_erro = 0; indice_erro < 6; indice_erro++) {
                double lista_phi_medido[QUANTIDADE_REPETICOES];
                double lista_erro_medido[QUANTIDADE_REPETICOES];
                double lista_bits_lidos[QUANTIDADE_REPETICOES];
                double lista_tempo_insercao_ns[QUANTIDADE_REPETICOES];
                double lista_tempo_consulta_ns[QUANTIDADE_REPETICOES];

                double phi_teorico = 0.0;
                double erro_teorico = 0.0;
                size_t total_bits = 0;
                size_t quantidade_hashes = 0;

                for (int numero_repeticao = 0; numero_repeticao < QUANTIDADE_REPETICOES; numero_repeticao++) {
                    /* Preparação das chaves fora do bloco cronometrado */
                    for (size_t indice = 0; indice < quantidade_elementos; indice++) {
                        gerar_chave_teste(chaves_inseridas[indice], tipo_distribuicao, numero_repeticao, 0, indice);
                    }
                    for (size_t indice = 0; indice < QUANTIDADE_CONSULTAS_AUSENTES; indice++) {
                        gerar_chave_teste(chaves_ausentes[indice], tipo_distribuicao, numero_repeticao, 1, indice);
                    }

                    FiltroBloom *filtro = filtro_criar_otimo(quantidade_elementos, taxas_erro_alvo[indice_erro]);

                    /* Mede o tempo médio de inserção */
                    double tempo_inicio_ns = obter_tempo_em_nanossegundos();
                    for (size_t indice = 0; indice < quantidade_elementos; indice++) {
                        filtro_inserir(filtro, chaves_inseridas[indice]);
                    }
                    lista_tempo_insercao_ns[numero_repeticao] =
                        (obter_tempo_em_nanossegundos() - tempo_inicio_ns) / (double)quantidade_elementos;

                    /* Mede o tempo médio de consulta e contabiliza falsos positivos e bits lidos */
                    size_t total_falsos_positivos = 0;
                    size_t soma_bits_lidos = 0;
                    tempo_inicio_ns = obter_tempo_em_nanossegundos();
                    for (size_t indice = 0; indice < QUANTIDADE_CONSULTAS_AUSENTES; indice++) {
                        size_t bits_lidos_nesta_consulta = 0;
                        if (filtro_consultar(filtro, chaves_ausentes[indice], &bits_lidos_nesta_consulta)) {
                            total_falsos_positivos++;
                        }
                        soma_bits_lidos += bits_lidos_nesta_consulta;
                    }
                    lista_tempo_consulta_ns[numero_repeticao] =
                        (obter_tempo_em_nanossegundos() - tempo_inicio_ns) / QUANTIDADE_CONSULTAS_AUSENTES;

                    lista_phi_medido[numero_repeticao] = filtro_phi_empirico(filtro);
                    lista_erro_medido[numero_repeticao] = (double)total_falsos_positivos / QUANTIDADE_CONSULTAS_AUSENTES;
                    lista_bits_lidos[numero_repeticao] = (double)soma_bits_lidos / QUANTIDADE_CONSULTAS_AUSENTES;

                    phi_teorico = filtro_phi_teorico(filtro);
                    erro_teorico = filtro_erro_teorico(filtro);
                    total_bits = filtro->total_bits;
                    quantidade_hashes = filtro->quantidade_hashes;

                    filtro_destruir(filtro);
                }

                double media_phi, desvio_phi;
                double media_erro, desvio_erro;
                double media_bits_lidos, desvio_bits_lidos;
                double media_tempo_insercao_ns, desvio_tempo_insercao_ns;
                double media_tempo_consulta_ns, desvio_tempo_consulta_ns;

                calcular_media_e_desvio(lista_phi_medido, QUANTIDADE_REPETICOES, &media_phi, &desvio_phi);
                calcular_media_e_desvio(lista_erro_medido, QUANTIDADE_REPETICOES, &media_erro, &desvio_erro);
                calcular_media_e_desvio(lista_bits_lidos, QUANTIDADE_REPETICOES, &media_bits_lidos, &desvio_bits_lidos);
                calcular_media_e_desvio(lista_tempo_insercao_ns, QUANTIDADE_REPETICOES,
                                        &media_tempo_insercao_ns, &desvio_tempo_insercao_ns);
                calcular_media_e_desvio(lista_tempo_consulta_ns, QUANTIDADE_REPETICOES,
                                        &media_tempo_consulta_ns, &desvio_tempo_consulta_ns);

                double bits_por_chave_bloom = (double)total_bits / (double)quantidade_elementos;
                /* Fórmula do método convencional do artigo para b = 64 bits e T = 4: (b+1)*(T+2)/(T-1) */
                double bits_por_chave_convencional = (BITS_POR_MENSAGEM_CONVENCIONAL + 1) * (4.0 + 2.0) / (4.0 - 1.0);

                fprintf(arquivo_csv,
                        "%s;%zu;%.6f;%zu;%zu;%.3f;%.1f;%.4f;%.4f;%.4f;%.5f;%.5f;%.5f;%.4f;%.4f;%.4f;%.1f;%.1f;%.1f;%.1f\n",
                        nomes_distribuicoes[tipo_distribuicao], quantidade_elementos, taxas_erro_alvo[indice_erro],
                        total_bits, quantidade_hashes, bits_por_chave_bloom, bits_por_chave_convencional,
                        phi_teorico, media_phi, desvio_phi, erro_teorico, media_erro, desvio_erro,
                        1.0 / phi_teorico, media_bits_lidos, desvio_bits_lidos,
                        media_tempo_insercao_ns, desvio_tempo_insercao_ns,
                        media_tempo_consulta_ns, desvio_tempo_consulta_ns);

                printf("%-10s %8zu %7.4f %9zu %2zu | %6.3f %6.3f | %8.5f %8.5f | %6.3f %6.3f | %8.1f\n",
                       nomes_distribuicoes[tipo_distribuicao], quantidade_elementos, taxas_erro_alvo[indice_erro],
                       total_bits, quantidade_hashes, phi_teorico, media_phi, erro_teorico, media_erro,
                       1.0 / phi_teorico, media_bits_lidos, media_tempo_consulta_ns);
                fflush(stdout);
            }

            free(chaves_inseridas);
            free(chaves_ausentes);
        }
    }

    fclose(arquivo_csv);
}

/*
 * Parte B: simula o caso prático da hifenização automática descrito por Bloom (1970).
 * De 500.000 palavras, 50.000 são exceções guardadas em disco e 450.000 seguem
 * regras simples. O filtro guarda as 50.000 exceções em memória e só acessamos
 * o disco quando o filtro aceita uma palavra.
 */
static void simular_caso_hifenizacao(void) {
    const size_t total_palavras = 500000;
    const size_t palavras_excecao = 50000;
    const size_t palavras_normais = total_palavras - palavras_excecao;

    FILE *arquivo_csv = fopen("resultados/hifenizacao.csv", "w");
    if (arquivo_csv == NULL) {
        perror("resultados/hifenizacao.csv");
        exit(1);
    }

    fprintf(arquivo_csv, "P_alvo;N_bits;d;acessos_disco;economia_acessos;falsos_positivos\n");
    printf("\n=== Parte B: hifenizacao (500000 palavras, 50000 excecoes no dicionario em disco) ===\n");
    printf("%7s %9s %2s %13s %10s\n", "P alvo", "N bits", "d", "acessos disco", "economia");

    char chave[TAMANHO_MAXIMO_CHAVE];
    for (int potencia = 1; potencia <= 6; potencia++) {
        double taxa_erro_alvo = 1.0 / (1 << potencia); /* Testa 1/2, 1/4, 1/8, 1/16, 1/32 e 1/64 */
        FiltroBloom *filtro = filtro_criar_otimo(palavras_excecao, taxa_erro_alvo);

        /* Guarda as 50.000 exceções no filtro em memória */
        for (size_t indice = 0; indice < palavras_excecao; indice++) {
            gerar_chave_teste(chave, 1, 0, 0, indice);
            filtro_inserir(filtro, chave);
        }

        /* Consulta as 450.000 palavras normais: qualquer aceitação gera um acesso desnecessário ao disco */
        size_t total_falsos_positivos = 0;
        for (size_t indice = 0; indice < palavras_normais; indice++) {
            gerar_chave_teste(chave, 1, 0, 1, indice);
            if (filtro_consultar(filtro, chave, NULL)) {
                total_falsos_positivos++;
            }
        }

        size_t total_acessos_disco = palavras_excecao + total_falsos_positivos;
        double economia_acessos = 1.0 - (double)total_acessos_disco / (double)total_palavras;

        fprintf(arquivo_csv, "%.6f;%zu;%zu;%zu;%.4f;%zu\n",
                taxa_erro_alvo, filtro->total_bits, filtro->quantidade_hashes,
                total_acessos_disco, economia_acessos, total_falsos_positivos);
        printf("%7.4f %9zu %2zu %13zu %9.1f%%\n",
               taxa_erro_alvo, filtro->total_bits, filtro->quantidade_hashes,
               total_acessos_disco, 100.0 * economia_acessos);

        filtro_destruir(filtro);
    }

    fclose(arquivo_csv);
}

int main(void) {
    executar_experimento_principal();
    simular_caso_hifenizacao();
    printf("\nResultados gravados em resultados/experimento.csv e resultados/hifenizacao.csv\n");
    return 0;
}
