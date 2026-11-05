#include "bloom.h" // Inclui as definições da estrutura e funções do Filtro de Bloom
#include <stdlib.h> // Inclui funções de alocação de memória (malloc, calloc, free)
#include <math.h>   // Inclui funções matemáticas (log2, ceil, pow)

// Define o valor de log2(e) caso o sistema não o defina por padrão no modo C11
#define LOG2_DE_E 1.44269504088896340736

// Função auxiliar simples para ligar (colocar em 1) um bit específico no vetor
static void ligar_bit(uint8_t *vetor_bits, size_t posicao_bit) {
    size_t indice_byte = posicao_bit / 8;         // Descobre em qual byte (grupo de 8 bits) o bit está
    size_t bit_dentro_do_byte = posicao_bit % 8;  // Descobre a posição exata (de 0 a 7) dentro desse byte
    uint8_t mascara = 1 << bit_dentro_do_byte;    // Cria uma máscara com apenas esse bit valendo 1
    vetor_bits[indice_byte] |= mascara;           // Usa o operador OU (|) para ligar o bit sem alterar os outros
}

// Função auxiliar simples para ler o valor (0 ou 1) de um bit específico no vetor
static bool ler_bit(const uint8_t *vetor_bits, size_t posicao_bit) {
    size_t indice_byte = posicao_bit / 8;         // Descobre em qual byte o bit está localizado
    size_t bit_dentro_do_byte = posicao_bit % 8;  // Descobre a posição exata (de 0 a 7) dentro desse byte
    uint8_t mascara = 1 << bit_dentro_do_byte;    // Cria uma máscara com apenas esse bit valendo 1
    return (vetor_bits[indice_byte] & mascara) != 0; // Usa o operador E (&) para checar se o bit está ligado
}

// Primeira função de hash (algoritmo FNV-1a): transforma os dados em um número inteiro grande
static uint64_t calcular_hash_1(const void *dados, size_t tamanho_dados) {
    const uint8_t *bytes = (const uint8_t *)dados; // Converte o ponteiro genérico para um vetor de bytes
    uint64_t valor_hash = 14695981039346656037ULL; // Valor inicial padrão do algoritmo FNV-1a
    for (size_t i = 0; i < tamanho_dados; i++) {   // Percorre cada byte do elemento recebido
        valor_hash ^= bytes[i];                    // Mistura o byte atual no hash usando OU exclusivo (XOR)
        valor_hash *= 1099511628211ULL;            // Multiplica por um número primo grande para espalhar os bits
    }
    return valor_hash;                             // Retorna o número final gerado pelo primeiro hash
}

// Segunda função de hash (algoritmo DJB2): gera um segundo número independente para o mesmo dado
static uint64_t calcular_hash_2(const void *dados, size_t tamanho_dados) {
    const uint8_t *bytes = (const uint8_t *)dados; // Converte o ponteiro genérico para um vetor de bytes
    uint64_t valor_hash = 5381ULL;                 // Valor inicial clássico do algoritmo DJB2
    for (size_t i = 0; i < tamanho_dados; i++) {   // Percorre cada byte do elemento recebido
        valor_hash = (valor_hash * 33) ^ bytes[i]; // Multiplica o acumulado por 33 e mistura com o byte atual
    }
    return valor_hash | 1ULL;                      // Garante que o resultado seja ímpar para espalhar melhor os passos
}

// Cria o filtro de Bloom com a quantidade de bits e de hashes informada
BloomFilter* bloom_create(size_t total_bits, size_t qtd_hashes) {
    if (total_bits == 0 || qtd_hashes == 0) {      // Verifica se os parâmetros são inválidos (zero)
        return NULL;                               // Retorna nulo caso não seja possível criar o filtro
    }

    BloomFilter *filtro = (BloomFilter *)malloc(sizeof(BloomFilter)); // Aloca memória para a estrutura do filtro
    if (filtro == NULL) {                          // Verifica se faltou memória ao alocar a estrutura
        return NULL;                               // Retorna nulo em caso de falha de alocação
    }

    size_t total_bytes = (total_bits + 7) / 8;     // Calcula quantos bytes são necessários para guardar todos os bits
    filtro->vetor_bits = (uint8_t *)calloc(total_bytes, sizeof(uint8_t)); // Aloca os bytes já zerados (todos os bits = 0)
    if (filtro->vetor_bits == NULL) {              // Verifica se faltou memória ao alocar o vetor de bits
        free(filtro);                              // Libera a estrutura que havia sido alocada antes
        return NULL;                               // Retorna nulo indicando falha
    }

    filtro->total_bits = total_bits;               // Guarda o total de bits na estrutura
    filtro->qtd_hashes = qtd_hashes;               // Guarda a quantidade de hashes na estrutura
    filtro->qtd_inseridos = 0;                     // Inicia o contador de elementos inseridos em zero
    return filtro;                                 // Retorna o ponteiro para o filtro pronto para uso
}

// Cria um filtro calculando automaticamente o número ideal de bits e de funções hash
BloomFilter* bloom_create_optimal(size_t elementos_esperados, double erro_maximo) {
    if (elementos_esperados == 0 || erro_maximo <= 0.0 || erro_maximo >= 1.0) { // Valida os limites de entrada
        return NULL;                               // Retorna nulo se a quantidade ou a taxa de erro forem inválidas
    }

    double log_negativo_erro = -log2(erro_maximo); // Calcula -log2(P''), base das fórmulas do artigo de Bloom
    size_t qtd_hashes = (size_t)ceil(log_negativo_erro); // Calcula d = teto de -log2(P'')
    size_t total_bits = (size_t)ceil((double)elementos_esperados * log_negativo_erro * LOG2_DE_E); // Calcula N'' ideal

    return bloom_create(total_bits, qtd_hashes);   // Cria e retorna o filtro com os valores ótimos calculados
}

// Libera a memória ocupada pelo filtro de Bloom
void bloom_destroy(BloomFilter *filtro) {
    if (filtro == NULL) {                          // Verifica se o ponteiro recebido já é nulo
        return;                                    // Se for nulo, não faz nada
    }
    free(filtro->vetor_bits);                      // Libera o vetor de bytes onde ficam os bits
    free(filtro);                                  // Libera a estrutura principal do filtro
}

// Insere um novo elemento dentro do filtro de Bloom
bool bloom_insert(BloomFilter *filtro, const void *dados, size_t tamanho_dados) {
    if (filtro == NULL || dados == NULL || tamanho_dados == 0) { // Verifica se os parâmetros são válidos
        return false;                              // Retorna falso se algum parâmetro for inválido
    }

    uint64_t hash1 = calcular_hash_1(dados, tamanho_dados); // Calcula o primeiro hash da chave
    uint64_t hash2 = calcular_hash_2(dados, tamanho_dados); // Calcula o segundo hash da chave

    for (size_t i = 0; i < filtro->qtd_hashes; i++) { // Repete para cada uma das 'd' posições de bit
        size_t posicao_bit = (hash1 + i * hash2) % filtro->total_bits; // Calcula a posição do bit dentro do limite do filtro
        ligar_bit(filtro->vetor_bits, posicao_bit); // Marca o bit calculado como 1 no vetor
    }

    filtro->qtd_inseridos++;                       // Incrementa o total de elementos inseridos
    return true;                                   // Retorna verdadeiro indicando sucesso na inserção
}

// Consulta se um elemento pertence ao filtro de Bloom
bool bloom_query(const BloomFilter *filtro, const void *dados, size_t tamanho_dados, size_t *bits_testados) {
    if (bits_testados != NULL) {                   // Verifica se o chamador passou um ponteiro para contar os bits lidos
        *bits_testados = 0;                        // Zera o contador de bits testados antes de começar a busca
    }

    if (filtro == NULL || dados == NULL || tamanho_dados == 0) { // Verifica se os parâmetros são válidos
        return false;                              // Retorna falso se algum dado de entrada for inválido
    }

    uint64_t hash1 = calcular_hash_1(dados, tamanho_dados); // Calcula o primeiro hash da chave buscada
    uint64_t hash2 = calcular_hash_2(dados, tamanho_dados); // Calcula o segundo hash da chave buscada

    for (size_t i = 0; i < filtro->qtd_hashes; i++) { // Percorre as 'd' posições de bit correspondentes à chave
        if (bits_testados != NULL) {               // Se o contador de bits testados foi fornecido
            (*bits_testados)++;                    // Soma 1 ao contador pois vamos testar mais um bit agora
        }

        size_t posicao_bit = (hash1 + i * hash2) % filtro->total_bits; // Calcula a posição do bit a ser verificado
        if (!ler_bit(filtro->vetor_bits, posicao_bit)) { // Verifica se o bit nessa posição vale 0
            return false;                          // Se achou um bit 0, o elemento com certeza NÃO está no filtro
        }
    }

    return true;                                   // Se todos os bits testados eram 1, o elemento provavelmente está no filtro
}

// Calcula a proporção real (empírica) de bits que permanecem valendo 0 no vetor
double bloom_empirical_phi(const BloomFilter *filtro) {
    if (filtro == NULL || filtro->total_bits == 0) { // Verifica se o filtro é válido
        return 0.0;                                // Retorna 0 caso o filtro seja inválido
    }

    size_t contagem_zeros = 0;                     // Variável para contar quantos bits valem 0
    for (size_t posicao = 0; posicao < filtro->total_bits; posicao++) { // Passa por todos os bits do filtro
        if (!ler_bit(filtro->vetor_bits, posicao)) { // Se o bit na posição atual estiver desligado (valendo 0)
            contagem_zeros++;                      // Aumenta em 1 a contagem de zeros encontrados
        }
    }

    return (double)contagem_zeros / (double)filtro->total_bits; // Divide o total de zeros pelo total de bits para achar a proporção
}

// Calcula a proporção teórica esperada de bits valendo 0 segundo a fórmula: (1 - d / N'')^n
double bloom_theoretical_phi(const BloomFilter *filtro) {
    if (filtro == NULL || filtro->total_bits == 0) { // Verifica se o filtro é válido
        return 0.0;                                // Retorna 0 caso o filtro seja inválido
    }

    double fracao_alterada = (double)filtro->qtd_hashes / (double)filtro->total_bits; // Calcula d / N''
    double base = 1.0 - fracao_alterada;           // Calcula (1 - d / N''), chance de um bit continuar 0 em uma inserção
    double expoente = (double)filtro->qtd_inseridos; // Pega o número 'n' de elementos inseridos até agora
    return pow(base, expoente);                    // Eleva a base ao expoente 'n' e retorna o resultado teórico
}
