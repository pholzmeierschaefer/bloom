/*
 * ============================================================================
 * MÓDULO DE EXEMPLO DIDÁTICO: tests/exemplo.c
 * ============================================================================
 *
 * O que este módulo faz:
 *   Cria um Filtro de Bloom bem pequeno (apenas 24 bits e 3 funções hash) para
 *   imprimir o vetor bit a bit na tela a cada inserção e consulta.
 *   É o mesmo exemplo ilustrado nos slides 6 e 7 da apresentação do seminário:
 *     - Inserções: "gato", "cao", "pato".
 *     - Consultas: "gato" (presente), "peixe" (rejeita em 1 bit),
 *       "galo" (rejeita em 2 bits) e "coelho" (falso positivo didático).
 * ============================================================================
 */

#include "filtro_bloom.h" /* Interface do Filtro de Bloom */
#include <stdio.h>        /* Função printf */

/*
 * Imprime todos os bits do filtro em uma única linha (da posição 0 até total_bits - 1).
 */
static void mostrar_vetor_de_bits(const FiltroBloom *filtro) {
    printf("   bits: ");
    for (size_t posicao_bit = 0; posicao_bit < filtro->total_bits; posicao_bit++) {
        int valor_bit = (filtro->vetor_de_bits[posicao_bit / 8] >> (posicao_bit % 8)) & 1;
        printf("%d", valor_bit);
    }
    printf("\n");
}

/*
 * Mostra na tela quais são as d posições de bit calculadas para uma chave específica.
 */
static void mostrar_enderecos_chave(const FiltroBloom *filtro, const char *chave) {
    printf("   '%s' usa os bits:", chave);
    for (size_t indice_hash = 0; indice_hash < filtro->quantidade_hashes; indice_hash++) {
        printf(" %zu", filtro_endereco(filtro, chave, indice_hash));
    }
    printf("\n");
}

int main(void) {
    const char *palavras_inseridas[] = {"gato", "cao", "pato"};
    const char *palavras_consultadas[] = {"gato", "peixe", "galo", "coelho"};

    /* Cria um filtro pequeno (N'' = 24 bits e d = 3 hashes) fácil de conferir à mão */
    FiltroBloom *filtro = filtro_criar(24, 3);

    printf("=== EXEMPLO PASSO A PASSO (N = 24 bits, d = 3) ===\n");
    printf("Estado inicial:\n");
    mostrar_vetor_de_bits(filtro);

    /* Passo 1: insere cada palavra e mostra o vetor atualizado após cada inserção */
    for (int indice = 0; indice < 3; indice++) {
        printf("\nInserindo '%s':\n", palavras_inseridas[indice]);
        mostrar_enderecos_chave(filtro, palavras_inseridas[indice]);
        filtro_inserir(filtro, palavras_inseridas[indice]);
        mostrar_vetor_de_bits(filtro);
    }

    /* Passo 2: consulta as 4 palavras e informa quantos bits foram lidos até decidir */
    printf("\nConsultas:\n");
    for (int indice = 0; indice < 4; indice++) {
        size_t quantidade_bits_lidos = 0;
        bool elemento_aceito = filtro_consultar(filtro, palavras_consultadas[indice], &quantidade_bits_lidos);
        mostrar_enderecos_chave(filtro, palavras_consultadas[indice]);
        printf("   -> %s (bits lidos: %zu)\n",
               elemento_aceito ? "ACEITA" : "REJEITADA",
               quantidade_bits_lidos);
    }

    /* Passo 3: mostra a comparação entre o phi'' medido e os valores teóricos do filtro */
    printf("\nphi medido = %.3f | phi previsto = %.3f | P previsto = %.3f\n",
           filtro_phi_empirico(filtro),
           filtro_phi_teorico(filtro),
           filtro_erro_teorico(filtro));

    filtro_destruir(filtro);
    return 0;
}
