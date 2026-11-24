#ifndef FILTRO_BLOOM_H /* Garante que este cabeçalho seja incluído apenas uma vez por compilação */
#define FILTRO_BLOOM_H /* Marca o cabeçalho como já incluído */

#include <stdbool.h> /* Fornece o tipo lógico bool e os valores true e false */
#include <stddef.h>  /* Fornece o tipo size_t, usado para tamanhos, índices e contagens */
#include <stdint.h>  /* Fornece inteiros de tamanho fixo: uint8_t (1 byte) e uint64_t (8 bytes) */

/*
 * ============================================================================
 * MÓDULO DE INTERFACE: FILTRO DE BLOOM (include/filtro_bloom.h)
 * ============================================================================
 *
 * O que é este módulo:
 *   Declara a estrutura de dados e todas as operações públicas do Filtro de
 *   Bloom ("Método 2" do artigo de Burton H. Bloom, 1970).
 *   Um Filtro de Bloom responde à pergunta: "esta chave pertence ao conjunto?"
 *   usando apenas um vetor compacto de bits em vez de guardar as chaves reais.
 *
 * Invariantes (regras que são SEMPRE verdadeiras durante todo o uso):
 *   I1. Monotonicidade: um bit que foi colocado em 1 nunca volta a valer 0
 *       (o Filtro de Bloom clássico não possui operação de remoção).
 *   I2. Ausência de falsos negativos: após inserir uma chave, todos os seus
 *       bits correspondentes passam a valer 1. Logo, consultar uma chave que
 *       já foi inserida SEMPRE retorna true ("aceita").
 *   I3. Rejeição com certeza / Aceitação probabilística: se ao menos um dos
 *       bits da chave valer 0, ela com certeza NUNCA foi inserida (retorna
 *       false). Se todos valerem 1, ela provavelmente foi inserida, mas pode
 *       ser um falso positivo causado por colisões com outras chaves.
 * ============================================================================
 */
typedef struct {
    size_t total_bits;           /* N'' do artigo: quantidade total de bits disponíveis no vetor */
    size_t quantidade_hashes;    /* d do artigo: quantas posições de bit cada chave liga/consulta */
    size_t quantidade_inseridos; /* n do artigo: quantos elementos já foram inseridos no filtro */
    uint8_t *vetor_de_bits;      /* Área de memória em bytes (cada byte armazena 8 bits), inicia zerada */
} FiltroBloom;

/*
 * Cria e inicializa um Filtro de Bloom com dimensões manuais.
 *   - total_bits: quantidade total de bits do filtro (N''). Deve ser > 0.
 *   - quantidade_hashes: quantidade de endereços gerados por chave (d). Deve ser > 0.
 * Retorna o ponteiro para o filtro criado, ou NULL se houver parâmetro 0 ou falta de memória.
 */
FiltroBloom *filtro_criar(size_t total_bits, size_t quantidade_hashes);

/*
 * Cria um Filtro de Bloom calculando automaticamente as dimensões ótimas (ponto
 * ótimo do artigo, onde metade dos bits fica em 0, ou seja, phi'' = 0,5).
 *   - quantidade_elementos: estimativa n de quantos itens serão guardados (> 0).
 *   - taxa_erro_permitida: probabilidade máxima P'' de falso positivo (0 < erro < 1).
 * Retorna o ponteiro para o filtro criado, ou NULL se os parâmetros forem inválidos.
 */
FiltroBloom *filtro_criar_otimo(size_t quantidade_elementos, double taxa_erro_permitida);

/*
 * Libera toda a memória alocada pelo filtro (o vetor de bits e a própria estrutura).
 * Aceita receber NULL com segurança (nesse caso, não faz nada).
 */
void filtro_destruir(FiltroBloom *filtro);

/*
 * Insere uma chave (texto terminado em '\0') no filtro.
 * Calcula os d endereços da chave, coloca todos esses bits em 1 e soma 1 em
 * quantidade_inseridos. Retorna true em caso de sucesso ou false se filtro/chave forem NULL.
 */
bool filtro_inserir(FiltroBloom *filtro, const char *chave);

/*
 * Consulta se uma chave possivelmente pertence ao conjunto.
 *   - bits_lidos: ponteiro opcional (pode ser NULL). Se fornecido, recebe quantos
 *     bits do vetor precisaram ser examinados nesta consulta (serve para medir T'').
 * Retorna true ("aceita": provavelmente pertence) ou false ("rejeitada": certamente ausente).
 */
bool filtro_consultar(const FiltroBloom *filtro, const char *chave, size_t *bits_lidos);

/*
 * Calcula e devolve o endereço (posição de bit entre 0 e total_bits - 1)
 * correspondente ao hash de número indice_hash (0 <= indice_hash < quantidade_hashes).
 * Útil para depuração e para mostrar o passo a passo da estrutura.
 */
size_t filtro_endereco(const FiltroBloom *filtro, const char *chave, size_t indice_hash);

/*
 * Percorre todo o vetor de bits e conta quantos bits estão ligados (valendo 1).
 */
size_t filtro_contar_uns(const FiltroBloom *filtro);

/*
 * Calcula o phi'' empírico (medido na prática): a fração real de bits no vetor
 * que ainda permanecem valendo 0 neste exato momento.
 */
double filtro_phi_empirico(const FiltroBloom *filtro);

/*
 * Calcula o phi'' teórico previsto pelo artigo: (1 - d / N'')^n,
 * que estima a proporção esperada de bits iguais a 0 após n inserções.
 */
double filtro_phi_teorico(const FiltroBloom *filtro);

/*
 * Calcula a probabilidade teórica P'' de falso positivo prevista pelo artigo:
 * (1 - phi'')^d, usando o phi'' teórico atual do filtro.
 */
double filtro_erro_teorico(const FiltroBloom *filtro);

#endif /* FILTRO_BLOOM_H */
