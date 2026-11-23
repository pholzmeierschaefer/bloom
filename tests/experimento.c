/*
 * Experimento: as fórmulas do artigo de Bloom (1970) preveem o que o filtro realmente faz?
 *
 * Parte A: varia n (3 tamanhos), P alvo (6 valores) e a distribuição das chaves (2 tipos).
 *          Mede φ'', P'' (falsos positivos), T'' (bits lidos por consulta ausente) e tempo.
 * Parte B: caso da hifenização do artigo (500.000 palavras, 50.000 exceções): acessos ao disco evitados.
 *
 * Chaves: geradas de forma determinística (a "semente" é o número da repetição), então o experimento é reproduzível.
 * Preparação dos dados (gerar chaves) fica fora do tempo medido.
 */
#include "filtro_bloom.h" /* filtro */
#include <math.h>         /* sqrt */
#include <stdio.h>        /* printf, fopen */
#include <stdlib.h>       /* malloc, free */
#include <time.h>         /* clock_gettime */

#define REPETICOES 10         /* quantas vezes cada configuração é repetida */
#define CONSULTAS 100000      /* chaves ausentes consultadas por repetição */
#define TAM_CHAVE 24          /* bytes reservados para cada chave */
#define BITS_MENSAGEM 64      /* b do artigo: tamanho de uma mensagem, usado só na comparação de espaço */

/* Média e desvio padrão amostral de um vetor. */
static void estatistica(const double *v, int n, double *media, double *desvio) {
    double soma = 0;                                   /* soma dos valores */
    for (int i = 0; i < n; i++) soma += v[i];          /* acumula */
    *media = soma / n;                                 /* média */
    double soma_q = 0;                                 /* soma dos quadrados dos desvios */
    for (int i = 0; i < n; i++) soma_q += (v[i] - *media) * (v[i] - *media); /* acumula */
    *desvio = sqrt(soma_q / (n - 1));                  /* desvio padrão amostral */
}

/* Hora atual em nanossegundos (relógio monotônico). */
static double agora_ns(void) {
    struct timespec t;                                 /* estrutura do relógio */
    clock_gettime(CLOCK_MONOTONIC, &t);                /* lê o relógio */
    return t.tv_sec * 1e9 + t.tv_nsec;                 /* converte para ns */
}

/* Embaralha 64 bits (SplitMix64): usado para gerar chaves "aleatórias" de forma reproduzível. */
static uint64_t misturar(uint64_t x) {
    x += 0x9e3779b97f4a7c15ULL;                        /* passo 1 */
    x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9ULL;       /* passo 2 */
    x = (x ^ (x >> 27)) * 0x94d049bb133111ebULL;       /* passo 3 */
    return x ^ (x >> 31);                              /* passo 4 */
}

/* Gera a chave i. grupo 0 = inseridas, 1 = ausentes. dist 0 = sequencial, 1 = aleatória (hex de 16 dígitos). */
static void gerar_chave(char *destino, int dist, int rep, int grupo, size_t i) {
    if (dist == 0) {                                   /* sequencial: i0_3_17 */
        snprintf(destino, TAM_CHAVE, "%c_%d_%zu", grupo ? 'a' : 'i', rep, i);
    } else {                                           /* aleatória */
        snprintf(destino, TAM_CHAVE, "%016llx", (unsigned long long)misturar(i + ((uint64_t)(rep * 2 + grupo) << 40)));
    }
}

/* Parte A. */
static void parte_a(void) {
    const size_t tamanhos[] = {10000, 100000, 1000000};              /* n */
    const double erros[] = {1.0 / 2, 1.0 / 4, 1.0 / 8, 1.0 / 16, 1.0 / 32, 1.0 / 64}; /* P alvo */
    const char *nome_dist[] = {"sequencial", "aleatoria"};           /* nomes das distribuições */
    FILE *csv = fopen("resultados/experimento.csv", "w");            /* arquivo de saída */
    if (csv == NULL) { perror("resultados/experimento.csv"); exit(1); } /* falha ao criar */
    fprintf(csv, "distribuicao;n;P_alvo;N_bits;d;bits_por_chave;bits_por_chave_convencional;"
                 "phi_teorico;phi_emp;phi_dp;P_teorico;P_emp;P_dp;T_teorico;T_emp;T_dp;ns_inserir;ns_inserir_dp;ns_consultar;ns_consultar_dp\n");
    printf("%-10s %8s %7s %9s %2s | %6s %6s | %8s %8s | %6s %6s | %8s\n",
           "dist", "n", "P alvo", "N bits", "d", "phi_t", "phi_e", "P_teor", "P_emp", "T_teo", "T_emp", "ns/cons");

    for (int dist = 0; dist < 2; dist++) {                           /* para cada distribuição */
        for (int a = 0; a < 3; a++) {                                /* para cada n */
            size_t n = tamanhos[a];                                  /* n atual */
            char (*dentro)[TAM_CHAVE] = malloc(n * TAM_CHAVE);       /* chaves inseridas */
            char (*fora)[TAM_CHAVE] = malloc(CONSULTAS * TAM_CHAVE); /* chaves ausentes */
            for (int b = 0; b < 6; b++) {                            /* para cada P alvo */
                double phi[REPETICOES], p[REPETICOES], t[REPETICOES], ns_ins[REPETICOES], ns_cons[REPETICOES];
                double phi_t = 0, p_t = 0;                           /* valores teóricos */
                size_t total_bits = 0, qtd_hashes = 0;               /* N'' e d */
                for (int rep = 0; rep < REPETICOES; rep++) {         /* repete o experimento */
                    for (size_t i = 0; i < n; i++) gerar_chave(dentro[i], dist, rep, 0, i);        /* preparação */
                    for (size_t i = 0; i < CONSULTAS; i++) gerar_chave(fora[i], dist, rep, 1, i);  /* preparação */
                    FiltroBloom *f = filtro_criar_otimo(n, erros[b]);                              /* filtro novo */

                    double ini = agora_ns();                         /* início da medição de inserção */
                    for (size_t i = 0; i < n; i++) filtro_inserir(f, dentro[i]);                   /* insere n chaves */
                    ns_ins[rep] = (agora_ns() - ini) / n;            /* ns por inserção */

                    size_t aceitas = 0, bits_lidos_total = 0;        /* falsos positivos e soma de bits lidos */
                    ini = agora_ns();                                /* início da medição de consulta */
                    for (size_t i = 0; i < CONSULTAS; i++) {         /* consulta chaves ausentes */
                        size_t lidos;                                /* bits lidos nesta consulta */
                        if (filtro_consultar(f, fora[i], &lidos)) aceitas++; /* falso positivo */
                        bits_lidos_total += lidos;                   /* soma */
                    }
                    ns_cons[rep] = (agora_ns() - ini) / CONSULTAS;   /* ns por consulta */

                    phi[rep] = filtro_phi_empirico(f);               /* φ'' medido */
                    p[rep] = (double)aceitas / CONSULTAS;            /* P'' medido */
                    t[rep] = (double)bits_lidos_total / CONSULTAS;   /* T'' medido */
                    phi_t = filtro_phi_teorico(f);                   /* φ'' previsto */
                    p_t = filtro_erro_teorico(f);                    /* P'' previsto */
                    total_bits = f->total_bits;                      /* N'' */
                    qtd_hashes = f->qtd_hashes;                      /* d */
                    filtro_destruir(f);                              /* libera o filtro */
                }
                double phi_m, phi_d, p_m, p_d, t_m, t_d, ins_m, ins_d, cons_m, cons_d;
                estatistica(phi, REPETICOES, &phi_m, &phi_d);        /* estatística de φ */
                estatistica(p, REPETICOES, &p_m, &p_d);              /* estatística de P */
                estatistica(t, REPETICOES, &t_m, &t_d);              /* estatística de T */
                estatistica(ns_ins, REPETICOES, &ins_m, &ins_d);     /* estatística do tempo de inserção */
                estatistica(ns_cons, REPETICOES, &cons_m, &cons_d);  /* estatística do tempo de consulta */
                double bits_chave = (double)total_bits / n;          /* bits por chave no filtro */
                double bits_conv = (BITS_MENSAGEM + 1) * (4 + 2) / (4.0 - 1); /* método convencional: (b+1)(T+2)/(T-1), T = 4 */
                fprintf(csv, "%s;%zu;%.6f;%zu;%zu;%.3f;%.1f;%.4f;%.4f;%.4f;%.5f;%.5f;%.5f;%.4f;%.4f;%.4f;%.1f;%.1f;%.1f;%.1f\n",
                        nome_dist[dist], n, erros[b], total_bits, qtd_hashes, bits_chave, bits_conv,
                        phi_t, phi_m, phi_d, p_t, p_m, p_d, 1.0 / phi_t, t_m, t_d, ins_m, ins_d, cons_m, cons_d);
                printf("%-10s %8zu %7.4f %9zu %2zu | %6.3f %6.3f | %8.5f %8.5f | %6.3f %6.3f | %8.1f\n",
                       nome_dist[dist], n, erros[b], total_bits, qtd_hashes, phi_t, phi_m, p_t, p_m, 1.0 / phi_t, t_m, cons_m);
                fflush(stdout);                                      /* mostra o progresso */
            }
            free(dentro);                                            /* libera chaves inseridas */
            free(fora);                                              /* libera chaves ausentes */
        }
    }
    fclose(csv);                                                     /* fecha o arquivo */
}

/* Parte B: aplicação do artigo (hifenização). */
static void parte_b(void) {
    const size_t total_palavras = 500000, excecoes = 50000;          /* números do artigo */
    const size_t consultas = total_palavras - excecoes;              /* palavras que NÃO estão no dicionário */
    FILE *csv = fopen("resultados/hifenizacao.csv", "w");            /* arquivo de saída */
    if (csv == NULL) { perror("resultados/hifenizacao.csv"); exit(1); } /* falha ao criar */
    fprintf(csv, "P_alvo;N_bits;d;acessos_disco;economia_acessos;falsos_positivos\n");
    printf("\n=== Parte B: hifenizacao (500000 palavras, 50000 excecoes no dicionario em disco) ===\n");
    printf("%7s %9s %2s %13s %10s\n", "P alvo", "N bits", "d", "acessos disco", "economia");
    char chave[TAM_CHAVE];                                           /* buffer da chave */
    for (int b = 1; b <= 6; b++) {                                   /* P = 1/2, 1/4, ... 1/64 */
        double erro = 1.0 / (1 << b);                                /* P alvo */
        FiltroBloom *f = filtro_criar_otimo(excecoes, erro);         /* filtro das exceções */
        for (size_t i = 0; i < excecoes; i++) {                      /* insere as palavras excepcionais */
            gerar_chave(chave, 1, 0, 0, i);                          /* chave aleatória reproduzível */
            filtro_inserir(f, chave);                                /* insere */
        }
        size_t falsos_positivos = 0;                                 /* palavras normais aceitas por engano */
        for (size_t i = 0; i < consultas; i++) {                     /* consulta as palavras normais */
            gerar_chave(chave, 1, 0, 1, i);                          /* chave ausente */
            if (filtro_consultar(f, chave, NULL)) falsos_positivos++; /* iria ao disco sem necessidade */
        }
        size_t acessos = excecoes + falsos_positivos;                /* exceções reais + falsos positivos */
        double economia = 1.0 - (double)acessos / total_palavras;    /* fração de acessos evitados */
        fprintf(csv, "%.6f;%zu;%zu;%zu;%.4f;%zu\n", erro, f->total_bits, f->qtd_hashes, acessos, economia, falsos_positivos);
        printf("%7.4f %9zu %2zu %13zu %9.1f%%\n", erro, f->total_bits, f->qtd_hashes, acessos, 100 * economia);
        filtro_destruir(f);                                          /* libera */
    }
    fclose(csv);                                                     /* fecha o arquivo */
}

int main(void) {
    parte_a();                                                       /* experimento principal */
    parte_b();                                                       /* caso do artigo */
    printf("\nResultados gravados em resultados/experimento.csv e resultados/hifenizacao.csv\n");
    return 0;                                                        /* sucesso */
}
