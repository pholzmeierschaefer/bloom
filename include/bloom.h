#ifndef BLOOM_H // Verifica se o cabeçalho BLOOM_H ainda não foi incluído
#define BLOOM_H // Define a macro BLOOM_H para evitar inclusões duplicadas

#include <stdint.h>  // Inclui tipos inteiros de tamanho fixo (como uint8_t e uint64_t)
#include <stdbool.h> // Inclui o tipo booleano (bool, true, false)
#include <stddef.h>  // Inclui o tipo size_t para representar tamanhos e contagens

// Estrutura que representa o Filtro de Bloom (Método 2 do artigo de Bloom de 1970)
typedef struct {
    size_t total_bits;      // Quantidade total de bits no filtro (chamado de N'' no artigo)
    size_t qtd_hashes;      // Quantidade de funções de hash usadas (chamado de d no artigo)
    size_t qtd_inseridos;   // Quantidade de elementos já inseridos no filtro (chamado de n no artigo)
    uint8_t *vetor_bits;    // Vetor de bytes onde cada bit individual será armazenado (1 byte = 8 bits)
} BloomFilter;

// Cria o filtro informando diretamente o total de bits e a quantidade de hashes
BloomFilter* bloom_create(size_t total_bits, size_t qtd_hashes);

// Cria o filtro calculando automaticamente o tamanho ideal a partir dos elementos esperados e erro máximo
BloomFilter* bloom_create_optimal(size_t elementos_esperados, double erro_maximo);

// Libera toda a memória alocada pelo filtro
void bloom_destroy(BloomFilter *filtro);

// Insere um elemento no filtro marcando seus bits correspondentes como 1
bool bloom_insert(BloomFilter *filtro, const void *dados, size_t tamanho_dados);

// Consulta se um elemento está no filtro e conta quantos bits foram verificados
bool bloom_query(const BloomFilter *filtro, const void *dados, size_t tamanho_dados, size_t *bits_testados);

// Calcula na prática a proporção de bits que continuam valendo 0 no filtro (phi empírico)
double bloom_empirical_phi(const BloomFilter *filtro);

// Calcula pela fórmula matemática a proporção esperada de bits valendo 0 (phi teórico)
double bloom_theoretical_phi(const BloomFilter *filtro);

#endif // Fim da proteção de inclusão do arquivo de cabeçalho
