/*
 * ============================================================================
 * MÓDULO DE TESTES DE CORREÇÃO: tests/teste_corretude.c
 * ============================================================================
 *
 * O que este módulo faz:
 *   Executa 10 testes automatizados usando a macro assert() para provar que a
 *   implementação do Filtro de Bloom funciona corretamente e respeita todas as
 *   invariantes e casos-limite do artigo.
 *
 * Distinção importante exigida pelo enunciado:
 *   - Defeitos da implementação (devem ser ZERO): quebra com entradas nulas,
 *     vazamento de memória, falsos negativos ou erro nas fórmulas ótimas.
 *   - Erros permitidos pelo método: falsos positivos (aceitar chaves que não
 *     foram inseridas), cuja taxa deve ficar próxima ao parâmetro P'' escolhido.
 * ============================================================================
 */

#include "filtro_bloom.h" /* Biblioteca do Filtro de Bloom que estamos testando */
#include <assert.h>       /* Macro assert(): interrompe o programa se alguma condição falhar */
#include <stdio.h>        /* Funções printf e snprintf */

static int contador_testes = 0; /* Numera automaticamente cada teste impresso na tela */

/*
 * Função auxiliar apenas para imprimir o título padronizado de cada teste.
 */
static void iniciar_teste(const char *descricao) {
    contador_testes++;
    printf("[T%d] %s\n", contador_testes, descricao);
}

/*
 * T1: Verifica proteção contra entradas inválidas.
 * Como funciona: tenta criar filtros com zeros ou taxas inválidas (0 ou 1) e
 * tenta inserir/consultar passando NULL. Nenhuma dessas chamadas pode travar.
 */
static void testar_entradas_invalidas(void) {
    iniciar_teste("entradas invalidas");
    assert(filtro_criar(0, 3) == NULL);
    assert(filtro_criar(100, 0) == NULL);
    assert(filtro_criar_otimo(0, 0.1) == NULL);
    assert(filtro_criar_otimo(100, 0.0) == NULL);
    assert(filtro_criar_otimo(100, 1.0) == NULL);

    FiltroBloom *filtro = filtro_criar(100, 3);
    assert(filtro != NULL);
    assert(!filtro_inserir(filtro, NULL));
    assert(!filtro_inserir(NULL, "a"));
    assert(!filtro_consultar(filtro, NULL, NULL));
    assert(!filtro_consultar(NULL, "a", NULL));

    filtro_destruir(filtro);
    filtro_destruir(NULL); /* Destruir ponteiro nulo não deve causar erro */
}

/*
 * T2: Verifica o comportamento de um filtro completamente vazio.
 * Como funciona: consulta uma chave qualquer sem ter inserido nada. O filtro
 * deve rejeitar no primeiro bit lido (quantidade_bits_lidos == 1) e phi'' deve ser 1.0.
 */
static void testar_filtro_vazio(void) {
    iniciar_teste("filtro vazio rejeita tudo lendo 1 bit");
    FiltroBloom *filtro = filtro_criar(1000, 4);
    size_t quantidade_bits_lidos = 0;

    assert(!filtro_consultar(filtro, "qualquer", &quantidade_bits_lidos));
    assert(quantidade_bits_lidos == 1);      /* Parou logo no 1º endereço pois era 0 */
    assert(filtro_contar_uns(filtro) == 0);  /* Nenhum bit pode estar ligado */
    assert(filtro_phi_empirico(filtro) == 1.0); /* 100% dos bits valem 0 */

    filtro_destruir(filtro);
}

/*
 * T3: Verifica se uma string vazia ("") funciona como chave válida.
 * Como funciona: insere "" e confirma que ela é aceita quando consultada.
 */
static void testar_chave_vazia(void) {
    iniciar_teste("chave vazia (\"\") pode ser inserida e encontrada");
    FiltroBloom *filtro = filtro_criar(1000, 4);
    assert(filtro_inserir(filtro, ""));
    assert(filtro_consultar(filtro, "", NULL));
    filtro_destruir(filtro);
}

/*
 * T4: Verifica um exemplo pequeno com resultado conferível manualmente.
 * Como funciona: insere a palavra "gato" em um filtro de 64 bits com 3 hashes.
 * Confirma que entre 1 e 3 bits foram ligados, que os bytes correspondentes aos
 * seus endereços não são zero, que a consulta retorna true e que o contador vale 1.
 */
static void testar_exemplo_manual(void) {
    iniciar_teste("exemplo manual: 1 chave liga no maximo d bits, exatamente os seus enderecos");
    FiltroBloom *filtro = filtro_criar(64, 3);
    assert(filtro_inserir(filtro, "gato"));

    size_t quantidade_bits_ligados = filtro_contar_uns(filtro);
    assert(quantidade_bits_ligados >= 1 && quantidade_bits_ligados <= 3);

    for (size_t indice_hash = 0; indice_hash < 3; indice_hash++) {
        size_t endereco = filtro_endereco(filtro, "gato", indice_hash);
        assert(filtro->vetor_de_bits[endereco / 8] != 0);
    }

    assert(filtro_consultar(filtro, "gato", NULL));
    assert(filtro->quantidade_inseridos == 1);
    filtro_destruir(filtro);
}

/*
 * T5: Verifica que inserções repetidas do mesmo elemento não alteram o vetor.
 * Como funciona: insere "repetida" 1 vez, anota quantos bits ficaram em 1 e
 * repete a inserção mais 99 vezes. O total de bits em 1 deve continuar idêntico.
 */
static void testar_elementos_repetidos(void) {
    iniciar_teste("inserir a mesma chave 100 vezes nao muda o vetor de bits");
    FiltroBloom *filtro = filtro_criar(500, 4);
    filtro_inserir(filtro, "repetida");
    size_t bits_ligados_antes = filtro_contar_uns(filtro);

    for (int indice = 0; indice < 99; indice++) {
        filtro_inserir(filtro, "repetida");
    }

    assert(filtro_contar_uns(filtro) == bits_ligados_antes);
    filtro_destruir(filtro);
}

/*
 * T6: Verifica a Invariante I2 (nunca pode haver falso negativo).
 * Como funciona: insere 10.000 chaves distintas e consulta todas as 10.000.
 * Todas precisam ser aceitas obrigatoriamente.
 */
static void testar_ausencia_falsos_negativos(void) {
    iniciar_teste("nenhum falso negativo (10000 chaves inseridas, todas encontradas)");
    FiltroBloom *filtro = filtro_criar_otimo(10000, 0.01);
    char chave[32];

    for (int indice = 0; indice < 10000; indice++) {
        snprintf(chave, sizeof chave, "chave%d", indice);
        assert(filtro_inserir(filtro, chave));
    }
    for (int indice = 0; indice < 10000; indice++) {
        snprintf(chave, sizeof chave, "chave%d", indice);
        assert(filtro_consultar(filtro, chave, NULL));
    }

    filtro_destruir(filtro);
}

/*
 * T7: Verifica a busca sem sucesso e o erro permitido pelo método.
 * Como funciona: projeta um filtro para erro P'' = 1/16 (6,25%), insere 10.000
 * chaves e consulta 100.000 chaves ausentes. A taxa de falsos positivos medida
 * deve permanecer próxima do alvo 0,0625.
 */
static void testar_busca_sem_sucesso(void) {
    iniciar_teste("busca sem sucesso: taxa de falsos positivos perto de P = 1/16");
    FiltroBloom *filtro = filtro_criar_otimo(10000, 1.0 / 16);
    char chave[32];

    for (int indice = 0; indice < 10000; indice++) {
        snprintf(chave, sizeof chave, "in%d", indice);
        filtro_inserir(filtro, chave);
    }

    int total_falsos_positivos = 0;
    for (int indice = 0; indice < 100000; indice++) {
        snprintf(chave, sizeof chave, "fora%d", indice);
        if (filtro_consultar(filtro, chave, NULL)) {
            total_falsos_positivos++;
        }
    }

    double taxa_falsos_positivos_medida = total_falsos_positivos / 100000.0;
    printf("      taxa medida = %.4f (alvo 0.0625)\n", taxa_falsos_positivos_medida);
    assert(taxa_falsos_positivos_medida > 0.0625 / 2 && taxa_falsos_positivos_medida < 0.0625 * 2);

    filtro_destruir(filtro);
}

/*
 * T8: Verifica o comportamento quando a capacidade é excedida (saturação).
 * Como funciona: insere 500 chaves em um filtro minúsculo de apenas 32 bits.
 * Quase todos os bits ficam ligados (phi'' < 0,05), gerando falso positivo para
 * chave ausente, mas as 500 chaves inseridas ainda assim continuam aceitas.
 */
static void testar_saturacao_capacidade(void) {
    iniciar_teste("saturacao: 32 bits recebendo 500 chaves aceita (quase) tudo, sem falso negativo");
    FiltroBloom *filtro = filtro_criar(32, 3);
    char chave[32];

    for (int indice = 0; indice < 500; indice++) {
        snprintf(chave, sizeof chave, "x%d", indice);
        filtro_inserir(filtro, chave);
    }

    assert(filtro_phi_empirico(filtro) < 0.05);
    assert(filtro_consultar(filtro, "ausente", NULL));

    for (int indice = 0; indice < 500; indice++) {
        snprintf(chave, sizeof chave, "x%d", indice);
        assert(filtro_consultar(filtro, chave, NULL));
    }

    filtro_destruir(filtro);
}

/*
 * T9: Verifica se filtro_criar_otimo reproduz os números do caso da hifenização do artigo.
 * Como funciona: para n = 50.000 palavras e P'' = 1/16, o artigo calcula que são
 * necessários d = 4 hashes e menos de 300.000 bits.
 */
static void testar_parametros_otimos_artigo(void) {
    iniciar_teste("parametros otimos: n=50000, P=1/16 -> d=4 e N menor que 300000 bits (artigo)");
    FiltroBloom *filtro = filtro_criar_otimo(50000, 1.0 / 16);

    assert(filtro->quantidade_hashes == 4);
    assert(filtro->total_bits > 280000 && filtro->total_bits < 300000);
    printf("      N = %zu bits, d = %zu\n", filtro->total_bits, filtro->quantidade_hashes);

    filtro_destruir(filtro);
}

/*
 * T10: Verifica se a proporção medida de bits em 0 (phi'') converge para ~0,5 no ponto ótimo.
 * Como funciona: cria um filtro ótimo para 20.000 chaves, insere todas elas e
 * compara o phi'' empírico com o phi'' teórico previsto pela fórmula.
 */
static void testar_proporcao_zeros_phi(void) {
    iniciar_teste("phi medido proximo de phi teorico (~0,5) no filtro otimo");
    FiltroBloom *filtro = filtro_criar_otimo(20000, 1.0 / 16);
    char chave[32];

    for (int indice = 0; indice < 20000; indice++) {
        snprintf(chave, sizeof chave, "k%d", indice);
        filtro_inserir(filtro, chave);
    }

    double phi_medido = filtro_phi_empirico(filtro);
    double phi_previsto = filtro_phi_teorico(filtro);
    printf("      phi medido = %.4f, phi previsto = %.4f\n", phi_medido, phi_previsto);
    assert(phi_medido > 0.45 && phi_medido < 0.55);
    assert(phi_medido > phi_previsto - 0.02 && phi_medido < phi_previsto + 0.02);

    filtro_destruir(filtro);
}

int main(void) {
    printf("=== TESTES DE CORRECAO DO FILTRO DE BLOOM ===\n");
    testar_entradas_invalidas();
    testar_filtro_vazio();
    testar_chave_vazia();
    testar_exemplo_manual();
    testar_elementos_repetidos();
    testar_ausencia_falsos_negativos();
    testar_busca_sem_sucesso();
    testar_saturacao_capacidade();
    testar_parametros_otimos_artigo();
    testar_proporcao_zeros_phi();
    printf("TODOS OS %d TESTES PASSARAM\n", contador_testes);
    return 0;
}
