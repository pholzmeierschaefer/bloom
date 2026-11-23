#ifndef FILTRO_BLOOM_H /* evita incluir este arquivo duas vezes */
#define FILTRO_BLOOM_H /* marca que o arquivo já foi incluído */

#include <stdbool.h> /* tipo bool (true / false) */
#include <stddef.h>  /* tipo size_t (tamanhos e contagens) */
#include <stdint.h>  /* tipos uint8_t e uint64_t */

/*
 * Filtro de Bloom = "Método 2" do artigo de Bloom (1970).
 *
 * Invariantes (sempre verdadeiros):
 *   I1. Um bit que vale 1 nunca volta a valer 0 (não existe remoção).
 *   I2. Depois de inserir uma chave, os d bits dela valem 1.
 *       Por isso NUNCA existe falso negativo.
 *   I3. Se algum dos d bits de uma chave vale 0, a chave com certeza NÃO foi inserida.
 *       Se os d bits valem 1, a chave "provavelmente" foi inserida (pode ser falso positivo).
 */
typedef struct {
    size_t total_bits;    /* N'' do artigo: quantidade de bits do vetor */
    size_t qtd_hashes;    /* d do artigo: quantos bits cada chave liga */
    size_t qtd_inseridos; /* n do artigo: quantas inserções já foram feitas */
    uint8_t *bits;        /* vetor de bits (8 bits por byte), começa todo em 0 */
} FiltroBloom;

/* Cria um filtro com total_bits bits e qtd_hashes hashes. Retorna NULL se algum valor for 0 ou faltar memória. */
FiltroBloom *filtro_criar(size_t total_bits, size_t qtd_hashes);

/* Cria o filtro ideal (φ = 1/2) para n chaves e erro máximo P (0 < P < 1). Retorna NULL se a entrada for inválida. */
FiltroBloom *filtro_criar_otimo(size_t n, double erro);

/* Libera a memória do filtro (aceita NULL). */
void filtro_destruir(FiltroBloom *filtro);

/* Insere a chave (texto terminado em '\0'). Retorna false se filtro ou chave forem NULL. */
bool filtro_inserir(FiltroBloom *filtro, const char *chave);

/* Consulta a chave. true = "aceita" (talvez pertença); false = "rejeitada" (certamente não pertence).
 * Se bits_lidos != NULL, recebe quantos bits foram examinados (usado para medir T''). */
bool filtro_consultar(const FiltroBloom *filtro, const char *chave, size_t *bits_lidos);

/* Retorna o endereço (posição do bit) de número i (0 <= i < d) que a chave usa. Útil para demonstrar o funcionamento. */
size_t filtro_endereco(const FiltroBloom *filtro, const char *chave, size_t i);

/* Conta quantos bits do vetor valem 1. */
size_t filtro_contar_uns(const FiltroBloom *filtro);

/* φ'' medido: fração de bits que valem 0 agora. */
double filtro_phi_empirico(const FiltroBloom *filtro);

/* φ'' previsto pelo artigo: (1 - d/N'')^n. */
double filtro_phi_teorico(const FiltroBloom *filtro);

/* P'' previsto pelo artigo: (1 - φ'')^d = probabilidade de falso positivo. */
double filtro_erro_teorico(const FiltroBloom *filtro);

#endif /* FILTRO_BLOOM_H */
