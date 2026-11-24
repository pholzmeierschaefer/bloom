/*
 * ============================================================================
 * MÓDULO DE IMPLEMENTAÇÃO: FILTRO DE BLOOM (src/filtro_bloom.c)
 * ============================================================================
 *
 * O que este módulo faz:
 *   Implementa todas as operações internas e públicas declaradas em
 *   include/filtro_bloom.h. O código é dividido em cinco partes:
 *
 *   1. Funções de Hash (hash duplo): transformam uma chave de texto em duas
 *      assinaturas numéricas de 64 bits (FNV-1a e DJB2) e as combinam para
 *      produzir quantos endereços de bits (d) forem necessários.
 *   2. Manipulação de Bits: funções auxiliares para ligar e ler um bit
 *      específico dentro de um vetor de bytes (já que C trabalha com bytes).
 *   3. Criação e Destruição: alocação segura de memória (iniciando tudo em 0),
 *      dimensionamento ótimo pela fórmula de Bloom (1970) e liberação final.
 *   4. Inserção e Consulta: o núcleo do algoritmo do artigo.
 *   5. Medições Estatísticas: funções para contar bits e comparar os valores
 *      medidos na prática com as equações teóricas do artigo.
 * ============================================================================
 */

#include "filtro_bloom.h" /* Declarações da estrutura e das funções públicas */
#include <math.h>         /* Funções matemáticas: log2, ceil (teto) e pow (potência) */
#include <stdlib.h>       /* Alocação dinâmica de memória: malloc, calloc e free */

/* Constante matemática log2(e) ≈ 1,442695, usada na fórmula do tamanho ideal N'' */
#define LOGARITMO_BASE2_DE_E 1.4426950408889634

/* ============================================================================
 * PARTE 1: FUNÇÕES DE HASH (GERAÇÃO DOS ENDEREÇOS NO VETOR DE BITS)
 * ============================================================================
 * Em vez de escrever d funções de hash totalmente diferentes, usamos a técnica
 * de "hash duplo": calculamos apenas dois hashes independentes (primeiro_hash
 * e segundo_hash) e geramos os d endereços pela fórmula:
 *   endereco(i) = (primeiro_hash + i * passo) mod total_bits
 */

/*
 * Primeira função de hash: algoritmo FNV-1a (Fowler-Noll-Vo, versão 64 bits).
 * Como funciona: começa com uma semente padrão fixa e, para cada caractere da
 * chave, mistura esse caractere com OU exclusivo (XOR) e multiplica por um
 * número primo grande para espalhar os bits de maneira uniforme.
 */
static uint64_t calcular_primeiro_hash_fnv1a(const char *chave) {
    uint64_t valor_hash = 14695981039346656037ULL; /* Semente inicial padrão do algoritmo FNV-1a */

    for (; *chave != '\0'; chave++) {              /* Percorre caractere por caractere até o fim do texto */
        valor_hash ^= (uint8_t)*chave;             /* Mistura o byte do caractere atual no hash (XOR) */
        valor_hash *= 1099511628211ULL;            /* Multiplica pelo primo padrão do FNV-1a */
    }

    return valor_hash;                             /* Devolve o número de 64 bits gerado */
}

/*
 * Segunda função de hash: algoritmo DJB2 (criado por Daniel J. Bernstein)
 * combinado com uma mistura final de bits (avalanche).
 * Como funciona: começa com 5381 e, a cada caractere, faz (hash * 33 + caractere).
 * No final, aplica deslocamentos e multiplicação por constante para evitar que
 * chaves muito parecidas (como "chave1" e "chave2") produzam passos parecidos.
 */
static uint64_t calcular_segundo_hash_djb2(const char *chave) {
    uint64_t valor_hash = 5381;                    /* Semente clássica escolhida por Daniel J. Bernstein */

    for (; *chave != '\0'; chave++) {              /* Percorre cada caractere da chave */
        valor_hash = valor_hash * 33 + (uint8_t)*chave; /* Acumula multiplicando por 33 e somando o byte */
    }

    /* Mistura final para garantir que pequenas mudanças na chave mudem bastante o resultado */
    valor_hash ^= valor_hash >> 33;
    valor_hash *= 0xff51afd7ed558ccdULL;
    valor_hash ^= valor_hash >> 33;

    return valor_hash;                             /* Devolve o segundo número de 64 bits */
}

/*
 * Combina os dois hashes para produzir o endereço do bit de número indice_hash
 * (onde indice_hash vai de 0 até quantidade_hashes - 1).
 * Como funciona: usa o segundo hash como tamanho do "passo" entre endereços.
 * Se o passo resultar em 0 após o módulo, força para 1 para evitar testar o
 * mesmo bit repetidamente d vezes.
 */
static size_t calcular_endereco_bit(uint64_t primeiro_hash,
                                    uint64_t segundo_hash,
                                    size_t indice_hash,
                                    size_t total_bits) {
    uint64_t passo = segundo_hash % total_bits; /* Restringe o passo ao tamanho do filtro */
    if (passo == 0) {
        passo = 1;                              /* Garante que o passo nunca seja nulo */
    }

    /* Avança "indice_hash" passos a partir do primeiro_hash e aplica módulo para caber no vetor */
    return (size_t)((primeiro_hash + indice_hash * passo) % total_bits);
}

/* ============================================================================
 * PARTE 2: MANIPULAÇÃO INDIVIDUAL DE BITS NO VETOR DE BYTES
 * ============================================================================
 * A memória em C é endereçada byte a byte (1 byte = 8 bits). Para guardar o
 * bit na posição "posicao_bit":
 *   - O byte onde ele mora é: posicao_bit / 8
 *   - A posição exata dentro desse byte (0 a 7) é: posicao_bit % 8
 */

/*
 * Coloca o bit na posição "posicao_bit" em 1, preservando os outros 7 bits do mesmo byte.
 */
static void ligar_bit(uint8_t *vetor_de_bits, size_t posicao_bit) {
    size_t indice_byte = posicao_bit / 8;          /* Descobre qual byte contém este bit */
    size_t deslocamento_bit = posicao_bit % 8;     /* Descobre qual dos 8 bits do byte alterar */
    uint8_t mascara = (uint8_t)(1u << deslocamento_bit); /* Cria máscara com 1 apenas nessa posição */

    vetor_de_bits[indice_byte] |= mascara;         /* Operação OU (|=) liga o bit sem apagar os vizinhos */
}

/*
 * Lê o valor do bit na posição "posicao_bit".
 * Retorna true se o bit estiver ligado (1), ou false se estiver desligado (0).
 */
static bool ler_bit(const uint8_t *vetor_de_bits, size_t posicao_bit) {
    size_t indice_byte = posicao_bit / 8;          /* Descobre qual byte contém este bit */
    size_t deslocamento_bit = posicao_bit % 8;     /* Descobre a posição dentro do byte */

    /* Desloca o bit desejado até a posição 0 e isola-o com (& 1) */
    return (vetor_de_bits[indice_byte] >> deslocamento_bit) & 1u;
}

/* ============================================================================
 * PARTE 3: CRIAÇÃO E DESTRUIÇÃO DO FILTRO
 * ============================================================================ */

/*
 * Aloca a estrutura do Filtro de Bloom e seu vetor de bits totalmente zerado.
 */
FiltroBloom *filtro_criar(size_t total_bits, size_t quantidade_hashes) {
    if (total_bits == 0 || quantidade_hashes == 0) {
        return NULL; /* Não faz sentido criar filtro sem bits ou sem funções hash */
    }

    FiltroBloom *filtro = malloc(sizeof(FiltroBloom));
    if (filtro == NULL) {
        return NULL; /* Falha ao alocar a estrutura principal por falta de memória */
    }

    /* Calcula quantos bytes inteiros são necessários para caber todos os total_bits
     * (soma 7 antes de dividir por 8 para arredondar para cima). calloc já zera tudo. */
    size_t total_bytes = (total_bits + 7) / 8;
    filtro->vetor_de_bits = calloc(total_bytes, sizeof(uint8_t));
    if (filtro->vetor_de_bits == NULL) {
        free(filtro); /* Evita vazamento de memória caso a segunda alocação falhe */
        return NULL;
    }

    filtro->total_bits = total_bits;
    filtro->quantidade_hashes = quantidade_hashes;
    filtro->quantidade_inseridos = 0;
    return filtro;
}

/*
 * Calcula N'' e d ótimos a partir da quantidade esperada de chaves (n) e da
 * taxa de erro desejada (P''), usando as equações do ponto ótimo (phi'' = 0,5)
 * demonstradas por Bloom (1970).
 */
FiltroBloom *filtro_criar_otimo(size_t quantidade_elementos, double taxa_erro_permitida) {
    if (quantidade_elementos == 0 || taxa_erro_permitida <= 0.0 || taxa_erro_permitida >= 1.0) {
        return NULL; /* Quantidade deve ser positiva e taxa de erro deve estar entre 0 e 1 */
    }

    double bits_por_chave = -log2(taxa_erro_permitida); /* Calcula -log2(P'') */
    size_t quantidade_hashes = (size_t)ceil(bits_por_chave); /* d = teto de -log2(P'') */

    /* N'' = teto de (n * (-log2 P'') * log2(e)) ≈ 1,44 * n * log2(1/P'') */
    size_t total_bits = (size_t)ceil((double)quantidade_elementos * bits_por_chave * LOGARITMO_BASE2_DE_E);

    return filtro_criar(total_bits, quantidade_hashes);
}

/*
 * Libera toda a memória usada pelo filtro.
 */
void filtro_destruir(FiltroBloom *filtro) {
    if (filtro == NULL) {
        return; /* Proteção: não tenta liberar um ponteiro nulo */
    }
    free(filtro->vetor_de_bits); /* Primeiro libera o vetor interno de bytes */
    free(filtro);                /* Depois libera a própria estrutura */
}

/* ============================================================================
 * PARTE 4: OPERAÇÕES PRINCIPAIS (INSERIR E CONSULTAR)
 * ============================================================================ */

/*
 * Insere uma chave no filtro ligando seus "quantidade_hashes" bits correspondentes.
 */
bool filtro_inserir(FiltroBloom *filtro, const char *chave) {
    if (filtro == NULL || chave == NULL) {
        return false; /* Recusa entradas nulas */
    }

    uint64_t primeiro_hash = calcular_primeiro_hash_fnv1a(chave);
    uint64_t segundo_hash = calcular_segundo_hash_djb2(chave);

    for (size_t indice_hash = 0; indice_hash < filtro->quantidade_hashes; indice_hash++) {
        size_t posicao_bit = calcular_endereco_bit(primeiro_hash, segundo_hash, indice_hash, filtro->total_bits);
        ligar_bit(filtro->vetor_de_bits, posicao_bit);
    }

    filtro->quantidade_inseridos++; /* Atualiza o contador de elementos inseridos (n) */
    return true;
}

/*
 * Verifica se uma chave pertence ao conjunto.
 * Como funciona: percorre os d endereços da chave em sequência. Assim que
 * encontra um bit igual a 0, interrompe a busca imediatamente (rejeição certa,
 * invariante I3) porque se a chave tivesse sido inserida, esse bit seria 1.
 * Se todos os d bits forem 1, retorna true (aceita como provável membro).
 */
bool filtro_consultar(const FiltroBloom *filtro, const char *chave, size_t *bits_lidos) {
    if (bits_lidos != NULL) {
        *bits_lidos = 0; /* Zera o contador de acessos antes de iniciar a verificação */
    }
    if (filtro == NULL || chave == NULL) {
        return false;
    }

    uint64_t primeiro_hash = calcular_primeiro_hash_fnv1a(chave);
    uint64_t segundo_hash = calcular_segundo_hash_djb2(chave);

    for (size_t indice_hash = 0; indice_hash < filtro->quantidade_hashes; indice_hash++) {
        if (bits_lidos != NULL) {
            (*bits_lidos)++; /* Contabiliza mais um bit examinado nesta consulta */
        }

        size_t posicao_bit = calcular_endereco_bit(primeiro_hash, segundo_hash, indice_hash, filtro->total_bits);
        if (!ler_bit(filtro->vetor_de_bits, posicao_bit)) {
            return false; /* Achou bit 0: rejeita imediatamente com 100% de certeza */
        }
    }

    return true; /* Todos os d bits valem 1: chave aceita (pertence ou falso positivo) */
}

/*
 * Expõe externamente o cálculo de um endereço específico de uma chave.
 */
size_t filtro_endereco(const FiltroBloom *filtro, const char *chave, size_t indice_hash) {
    uint64_t primeiro_hash = calcular_primeiro_hash_fnv1a(chave);
    uint64_t segundo_hash = calcular_segundo_hash_djb2(chave);
    return calcular_endereco_bit(primeiro_hash, segundo_hash, indice_hash, filtro->total_bits);
}

/* ============================================================================
 * PARTE 5: MEDIÇÕES EMPÍRICAS E FÓRMULAS TEÓRICAS DO ARTIGO
 * ============================================================================ */

/*
 * Conta quantos bits do vetor valem 1 no momento atual.
 */
size_t filtro_contar_uns(const FiltroBloom *filtro) {
    size_t quantidade_uns = 0;
    for (size_t posicao_bit = 0; posicao_bit < filtro->total_bits; posicao_bit++) {
        if (ler_bit(filtro->vetor_de_bits, posicao_bit)) {
            quantidade_uns++;
        }
    }
    return quantidade_uns;
}

/*
 * Calcula a fração real de bits que continuam valendo 0 (phi'' empírico).
 */
double filtro_phi_empirico(const FiltroBloom *filtro) {
    size_t quantidade_zeros = filtro->total_bits - filtro_contar_uns(filtro);
    return (double)quantidade_zeros / (double)filtro->total_bits;
}

/*
 * Calcula a fração esperada de bits valendo 0 segundo o artigo:
 *   phi'' = (1 - d / N'')^n
 */
double filtro_phi_teorico(const FiltroBloom *filtro) {
    double probabilidade_continuar_zero_em_um_passo =
        1.0 - (double)filtro->quantidade_hashes / (double)filtro->total_bits;
    return pow(probabilidade_continuar_zero_em_um_passo, (double)filtro->quantidade_inseridos);
}

/*
 * Calcula a probabilidade teórica de falso positivo segundo o artigo:
 *   P'' = (1 - phi'')^d
 */
double filtro_erro_teorico(const FiltroBloom *filtro) {
    double proporcao_uns_teorica = 1.0 - filtro_phi_teorico(filtro);
    return pow(proporcao_uns_teorica, (double)filtro->quantidade_hashes);
}
