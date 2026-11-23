#include "filtro_bloom.h" /* filtro */
#include <stdio.h>       /* printf */

/* Mostra o vetor de bits em uma linha (posição 0 à esquerda). */
static void mostrar_bits(const FiltroBloom *f) {
    printf("   bits: ");                                          /* rótulo */
    for (size_t pos = 0; pos < f->total_bits; pos++) {            /* para cada posição */
        printf("%d", (f->bits[pos / 8] >> (pos % 8)) & 1);        /* imprime 0 ou 1 */
    }
    printf("\n");                                                 /* fim da linha */
}

/* Mostra os endereços (bits) que uma chave usa. */
static void mostrar_enderecos(const FiltroBloom *f, const char *chave) {
    printf("   '%s' usa os bits:", chave);                        /* rótulo */
    for (size_t i = 0; i < f->qtd_hashes; i++) {                  /* para cada endereço */
        printf(" %zu", filtro_endereco(f, chave, i));             /* imprime o endereço */
    }
    printf("\n");                                                 /* fim da linha */
}

int main(void) {
    const char *inseridas[] = {"gato", "cao", "pato"};            /* chaves que vamos guardar */
    const char *consultadas[] = {"gato", "peixe", "galo", "coelho"}; /* chaves buscadas */
    FiltroBloom *f = filtro_criar(24, 3);                         /* filtro pequeno: N = 24 bits, d = 3 */

    printf("=== EXEMPLO PASSO A PASSO (N = 24 bits, d = 3) ===\n"); /* título */
    printf("Estado inicial:\n");                                  /* antes de inserir */
    mostrar_bits(f);                                              /* tudo 0 */

    for (int i = 0; i < 3; i++) {                                 /* insere cada chave */
        printf("\nInserindo '%s':\n", inseridas[i]);              /* mensagem */
        mostrar_enderecos(f, inseridas[i]);                       /* endereços da chave */
        filtro_inserir(f, inseridas[i]);                          /* liga os bits */
        mostrar_bits(f);                                          /* mostra o vetor */
    }

    printf("\nConsultas:\n");                                     /* consultas */
    for (int i = 0; i < 4; i++) {                                 /* para cada chave buscada */
        size_t lidos = 0;                                         /* bits lidos */
        bool aceita = filtro_consultar(f, consultadas[i], &lidos);/* consulta */
        mostrar_enderecos(f, consultadas[i]);                     /* endereços */
        printf("   -> %s (bits lidos: %zu)\n", aceita ? "ACEITA" : "REJEITADA", lidos); /* resultado */
    }
    printf("\nphi medido = %.3f | phi previsto = %.3f | P previsto = %.3f\n",
           filtro_phi_empirico(f), filtro_phi_teorico(f), filtro_erro_teorico(f)); /* medidas */

    filtro_destruir(f);                                           /* libera */
    return 0;                                                     /* sucesso */
}
