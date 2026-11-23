#include "filtro_bloom.h" /* declarações do filtro */
#include <math.h>        /* log2, ceil, pow */
#include <stdlib.h>      /* malloc, calloc, free */

#define LOG2_E 1.4426950408889634 /* log2(e), usado na fórmula do tamanho ideal */

/* ---------- Funções de hash (duas, para gerar os d endereços) ---------- */

/* Hash 1: FNV-1a de 64 bits. */
static uint64_t hash_fnv(const char *chave) {
    uint64_t h = 14695981039346656037ULL; /* valor inicial do FNV-1a */
    for (; *chave != '\0'; chave++) {     /* para cada caractere da chave */
        h ^= (uint8_t)*chave;             /* mistura o caractere no hash */
        h *= 1099511628211ULL;            /* multiplica por um primo grande */
    }
    return h;                             /* devolve o hash 1 */
}

/* Hash 2: DJB2 de 64 bits, com uma mistura final para espalhar melhor os bits. */
static uint64_t hash_djb(const char *chave) {
    uint64_t h = 5381;                    /* valor inicial do DJB2 */
    for (; *chave != '\0'; chave++) {     /* para cada caractere da chave */
        h = h * 33 + (uint8_t)*chave;     /* h = h*33 + caractere */
    }
    h ^= h >> 33;                         /* mistura final: passo 1 */
    h *= 0xff51afd7ed558ccdULL;           /* mistura final: passo 2 */
    h ^= h >> 33;                         /* mistura final: passo 3 */
    return h;                             /* devolve o hash 2 */
}

/* Endereço i da chave: (hash1 + i * passo) mod N, onde passo vem do hash 2 (nunca 0). */
static size_t calcular_endereco(uint64_t h1, uint64_t h2, size_t i, size_t total_bits) {
    uint64_t passo = h2 % total_bits;                  /* passo entre os endereços */
    if (passo == 0) passo = 1;                         /* passo 0 repetiria o mesmo bit d vezes */
    return (size_t)((h1 + i * passo) % total_bits);    /* endereço do i-ésimo bit */
}

/* ---------- Acesso a um bit do vetor ---------- */

/* Liga (coloca em 1) o bit de número pos. */
static void ligar_bit(uint8_t *bits, size_t pos) {
    bits[pos / 8] |= (uint8_t)(1u << (pos % 8)); /* byte = pos/8; bit dentro do byte = pos%8 */
}

/* Lê o bit de número pos (true se valer 1). */
static bool ler_bit(const uint8_t *bits, size_t pos) {
    return (bits[pos / 8] >> (pos % 8)) & 1u;    /* desloca o bit para a posição 0 e isola */
}

/* ---------- Criação e destruição ---------- */

FiltroBloom *filtro_criar(size_t total_bits, size_t qtd_hashes) {
    if (total_bits == 0 || qtd_hashes == 0) return NULL;   /* parâmetros inválidos */
    FiltroBloom *filtro = malloc(sizeof(FiltroBloom));      /* aloca a estrutura */
    if (filtro == NULL) return NULL;                        /* sem memória */
    filtro->bits = calloc((total_bits + 7) / 8, 1);         /* aloca os bytes já zerados (todos os bits = 0) */
    if (filtro->bits == NULL) {                             /* sem memória para os bits */
        free(filtro);                                       /* desfaz a primeira alocação */
        return NULL;                                        /* informa a falha */
    }
    filtro->total_bits = total_bits;                        /* guarda N'' */
    filtro->qtd_hashes = qtd_hashes;                        /* guarda d */
    filtro->qtd_inseridos = 0;                              /* nenhuma inserção ainda */
    return filtro;                                          /* filtro pronto */
}

FiltroBloom *filtro_criar_otimo(size_t n, double erro) {
    if (n == 0 || erro <= 0.0 || erro >= 1.0) return NULL; /* entrada inválida */
    double bits_por_chave = -log2(erro);                    /* -log2(P'') */
    size_t qtd_hashes = (size_t)ceil(bits_por_chave);       /* d = -log2(P'') arredondado para cima */
    size_t total_bits = (size_t)ceil(n * bits_por_chave * LOG2_E); /* N'' = n * (-log2 P'') * log2(e) */
    return filtro_criar(total_bits, qtd_hashes);            /* cria com os valores calculados */
}

void filtro_destruir(FiltroBloom *filtro) {
    if (filtro == NULL) return; /* nada a liberar */
    free(filtro->bits);         /* libera o vetor de bits */
    free(filtro);               /* libera a estrutura */
}

/* ---------- Operações do artigo: inserir e consultar ---------- */

bool filtro_inserir(FiltroBloom *filtro, const char *chave) {
    if (filtro == NULL || chave == NULL) return false;      /* entrada inválida */
    uint64_t h1 = hash_fnv(chave);                          /* hash 1 da chave */
    uint64_t h2 = hash_djb(chave);                          /* hash 2 da chave */
    for (size_t i = 0; i < filtro->qtd_hashes; i++) {       /* para cada um dos d endereços */
        ligar_bit(filtro->bits, calcular_endereco(h1, h2, i, filtro->total_bits)); /* liga o bit */
    }
    filtro->qtd_inseridos++;                                /* conta mais uma inserção */
    return true;                                            /* sucesso */
}

bool filtro_consultar(const FiltroBloom *filtro, const char *chave, size_t *bits_lidos) {
    if (bits_lidos != NULL) *bits_lidos = 0;                /* ainda não leu nenhum bit */
    if (filtro == NULL || chave == NULL) return false;      /* entrada inválida */
    uint64_t h1 = hash_fnv(chave);                          /* hash 1 da chave */
    uint64_t h2 = hash_djb(chave);                          /* hash 2 da chave */
    for (size_t i = 0; i < filtro->qtd_hashes; i++) {       /* para cada um dos d endereços */
        if (bits_lidos != NULL) (*bits_lidos)++;            /* conta o bit que será lido */
        if (!ler_bit(filtro->bits, calcular_endereco(h1, h2, i, filtro->total_bits))) {
            return false;                                   /* achou um 0: rejeita na hora (invariante I3) */
        }
    }
    return true;                                            /* todos os d bits valem 1: aceita */
}

size_t filtro_endereco(const FiltroBloom *filtro, const char *chave, size_t i) {
    return calcular_endereco(hash_fnv(chave), hash_djb(chave), i, filtro->total_bits); /* endereço i da chave */
}

/* ---------- Medidas usadas nos testes e no experimento ---------- */

size_t filtro_contar_uns(const FiltroBloom *filtro) {
    size_t uns = 0;                                         /* contador de bits 1 */
    for (size_t pos = 0; pos < filtro->total_bits; pos++) { /* para cada bit do vetor */
        if (ler_bit(filtro->bits, pos)) uns++;              /* conta se valer 1 */
    }
    return uns;                                             /* total de bits 1 */
}

double filtro_phi_empirico(const FiltroBloom *filtro) {
    size_t zeros = filtro->total_bits - filtro_contar_uns(filtro); /* bits que valem 0 */
    return (double)zeros / (double)filtro->total_bits;      /* fração de zeros */
}

double filtro_phi_teorico(const FiltroBloom *filtro) {
    double chance_continuar_zero = 1.0 - (double)filtro->qtd_hashes / (double)filtro->total_bits; /* 1 - d/N'' */
    return pow(chance_continuar_zero, (double)filtro->qtd_inseridos); /* (1 - d/N'')^n */
}

double filtro_erro_teorico(const FiltroBloom *filtro) {
    return pow(1.0 - filtro_phi_teorico(filtro), (double)filtro->qtd_hashes); /* (1 - φ'')^d */
}
