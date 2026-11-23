#include "filtro_bloom.h" /* filtro que será testado */
#include <assert.h>      /* assert: aborta o programa se a condição for falsa */
#include <stdio.h>       /* printf, snprintf */

static int numero_teste = 0; /* contador para numerar a saída */

/* Imprime o cabeçalho de cada teste. */
static void iniciar(const char *descricao) {
    printf("[T%d] %s\n", ++numero_teste, descricao); /* ex.: [T1] entradas inválidas */
}

/* T1: entradas inválidas não podem quebrar o programa. */
static void teste_entradas_invalidas(void) {
    iniciar("entradas invalidas");
    assert(filtro_criar(0, 3) == NULL);               /* 0 bits */
    assert(filtro_criar(100, 0) == NULL);             /* 0 hashes */
    assert(filtro_criar_otimo(0, 0.1) == NULL);       /* n = 0 */
    assert(filtro_criar_otimo(100, 0.0) == NULL);     /* erro = 0 */
    assert(filtro_criar_otimo(100, 1.0) == NULL);     /* erro = 1 */
    FiltroBloom *f = filtro_criar(100, 3);            /* filtro válido */
    assert(f != NULL);                                /* deve ser criado */
    assert(!filtro_inserir(f, NULL));                 /* chave NULL é recusada */
    assert(!filtro_inserir(NULL, "a"));               /* filtro NULL é recusado */
    assert(!filtro_consultar(f, NULL, NULL));         /* consulta com chave NULL */
    assert(!filtro_consultar(NULL, "a", NULL));       /* consulta com filtro NULL */
    filtro_destruir(f);                               /* libera */
    filtro_destruir(NULL);                            /* não deve quebrar */
}

/* T2: filtro vazio (entrada vazia): tudo é rejeitado no 1º bit lido. */
static void teste_filtro_vazio(void) {
    iniciar("filtro vazio rejeita tudo lendo 1 bit");
    FiltroBloom *f = filtro_criar(1000, 4);           /* filtro vazio */
    size_t lidos = 0;                                 /* recebe quantos bits foram lidos */
    assert(!filtro_consultar(f, "qualquer", &lidos)); /* nada foi inserido, logo rejeita */
    assert(lidos == 1);                               /* parou no primeiro bit (era 0) */
    assert(filtro_contar_uns(f) == 0);                /* nenhum bit ligado */
    assert(filtro_phi_empirico(f) == 1.0);            /* φ = 1: todos os bits valem 0 */
    filtro_destruir(f);                               /* libera */
}

/* T3: chave vazia "" também é uma mensagem válida. */
static void teste_chave_vazia(void) {
    iniciar("chave vazia (\"\") pode ser inserida e encontrada");
    FiltroBloom *f = filtro_criar(1000, 4);           /* filtro vazio */
    assert(filtro_inserir(f, ""));                    /* insere a string vazia */
    assert(filtro_consultar(f, "", NULL));            /* e ela é encontrada */
    filtro_destruir(f);                               /* libera */
}

/* T4: exemplo manual pequeno, com resultado verificável à mão. */
static void teste_exemplo_manual(void) {
    iniciar("exemplo manual: 1 chave liga no maximo d bits, exatamente os seus enderecos");
    FiltroBloom *f = filtro_criar(64, 3);             /* 64 bits, d = 3 */
    assert(filtro_inserir(f, "gato"));                /* insere "gato" */
    size_t uns = filtro_contar_uns(f);                /* quantos bits foram ligados */
    assert(uns >= 1 && uns <= 3);                     /* no máximo d = 3 (menos se houver coincidência) */
    for (size_t i = 0; i < 3; i++) {                  /* para cada endereço de "gato" */
        assert(f->bits[filtro_endereco(f, "gato", i) / 8] != 0); /* o byte desse bit não é zero */
    }
    assert(filtro_consultar(f, "gato", NULL));        /* "gato" é aceito */
    assert(f->qtd_inseridos == 1);                    /* uma inserção contada */
    filtro_destruir(f);                               /* libera */
}

/* T5: elementos repetidos não ligam bits novos. */
static void teste_repetidos(void) {
    iniciar("inserir a mesma chave 100 vezes nao muda o vetor de bits");
    FiltroBloom *f = filtro_criar(500, 4);            /* filtro pequeno */
    filtro_inserir(f, "repetida");                    /* primeira inserção */
    size_t uns_antes = filtro_contar_uns(f);          /* bits ligados após 1 inserção */
    for (int i = 0; i < 99; i++) filtro_inserir(f, "repetida"); /* mais 99 inserções iguais */
    assert(filtro_contar_uns(f) == uns_antes);        /* nenhum bit novo */
    filtro_destruir(f);                               /* libera */
}

/* T6: invariante I2 — nenhum falso negativo (defeito, não erro permitido). */
static void teste_sem_falsos_negativos(void) {
    iniciar("nenhum falso negativo (10000 chaves inseridas, todas encontradas)");
    FiltroBloom *f = filtro_criar_otimo(10000, 0.01); /* P = 1% */
    char chave[32];                                   /* buffer para montar as chaves */
    for (int i = 0; i < 10000; i++) {                 /* insere 10000 chaves */
        snprintf(chave, sizeof chave, "chave%d", i);  /* chave0, chave1, ... */
        assert(filtro_inserir(f, chave));             /* inserção ok */
    }
    for (int i = 0; i < 10000; i++) {                 /* consulta as mesmas chaves */
        snprintf(chave, sizeof chave, "chave%d", i);  /* mesma chave */
        assert(filtro_consultar(f, chave, NULL));     /* TEM de ser aceita */
    }
    filtro_destruir(f);                               /* libera */
}

/* T7: busca sem sucesso — falsos positivos são erro PERMITIDO, e devem ficar perto de P. */
static void teste_busca_sem_sucesso(void) {
    iniciar("busca sem sucesso: taxa de falsos positivos perto de P = 1/16");
    FiltroBloom *f = filtro_criar_otimo(10000, 1.0 / 16); /* P = 6,25% */
    char chave[32];                                   /* buffer para as chaves */
    for (int i = 0; i < 10000; i++) {                 /* insere 10000 chaves "in..." */
        snprintf(chave, sizeof chave, "in%d", i);     /* in0, in1, ... */
        filtro_inserir(f, chave);                     /* insere */
    }
    int falsos_positivos = 0;                         /* aceitas por engano */
    for (int i = 0; i < 100000; i++) {                /* consulta 100000 chaves ausentes */
        snprintf(chave, sizeof chave, "fora%d", i);   /* fora0, fora1, ... */
        if (filtro_consultar(f, chave, NULL)) falsos_positivos++; /* conta o erro permitido */
    }
    double taxa = falsos_positivos / 100000.0;        /* taxa medida */
    printf("      taxa medida = %.4f (alvo 0.0625)\n", taxa); /* mostra o valor */
    assert(taxa > 0.0625 / 2 && taxa < 0.0625 * 2);   /* perto do alvo (fator 2) */
    filtro_destruir(f);                               /* libera */
}

/* T8: capacidade acima do limite — filtro saturado aceita tudo, mas continua sem falso negativo. */
static void teste_saturacao(void) {
    iniciar("saturacao: 32 bits recebendo 500 chaves aceita (quase) tudo, sem falso negativo");
    FiltroBloom *f = filtro_criar(32, 3);             /* filtro minúsculo */
    char chave[32];                                   /* buffer */
    for (int i = 0; i < 500; i++) {                   /* insere muito além da capacidade */
        snprintf(chave, sizeof chave, "x%d", i);      /* x0, x1, ... */
        filtro_inserir(f, chave);                     /* insere */
    }
    assert(filtro_phi_empirico(f) < 0.05);            /* quase nenhum bit 0 sobrou */
    assert(filtro_consultar(f, "ausente", NULL));     /* falso positivo certo */
    for (int i = 0; i < 500; i++) {                   /* e as chaves inseridas continuam aceitas */
        snprintf(chave, sizeof chave, "x%d", i);      /* mesma chave */
        assert(filtro_consultar(f, chave, NULL));     /* invariante I2 */
    }
    filtro_destruir(f);                               /* libera */
}

/* T9: filtro_criar_otimo segue as fórmulas do artigo (caso da hifenização: 50.000 palavras, P = 1/16). */
static void teste_parametros_otimos(void) {
    iniciar("parametros otimos: n=50000, P=1/16 -> d=4 e N menor que 300000 bits (artigo)");
    FiltroBloom *f = filtro_criar_otimo(50000, 1.0 / 16); /* caso do artigo */
    assert(f->qtd_hashes == 4);                       /* d = -log2(1/16) = 4 */
    assert(f->total_bits > 280000 && f->total_bits < 300000); /* N'' ~ 288.540 */
    printf("      N = %zu bits, d = %zu\n", f->total_bits, f->qtd_hashes); /* mostra os valores */
    filtro_destruir(f);                               /* libera */
}

/* T10: após inserir n chaves, φ medido fica perto de φ previsto (≈ 0,5 no filtro ótimo). */
static void teste_phi(void) {
    iniciar("phi medido proximo de phi teorico (~0,5) no filtro otimo");
    FiltroBloom *f = filtro_criar_otimo(20000, 1.0 / 16); /* filtro ótimo, d = 4 exato */
    char chave[32];                                   /* buffer */
    for (int i = 0; i < 20000; i++) {                 /* insere n chaves */
        snprintf(chave, sizeof chave, "k%d", i);      /* k0, k1, ... */
        filtro_inserir(f, chave);                     /* insere */
    }
    double medido = filtro_phi_empirico(f);           /* φ medido */
    double previsto = filtro_phi_teorico(f);          /* φ previsto */
    printf("      phi medido = %.4f, phi previsto = %.4f\n", medido, previsto); /* mostra */
    assert(medido > 0.45 && medido < 0.55);           /* perto de 0,5 */
    assert(medido > previsto - 0.02 && medido < previsto + 0.02); /* perto da fórmula */
    filtro_destruir(f);                               /* libera */
}

int main(void) {
    printf("=== TESTES DE CORRECAO DO FILTRO DE BLOOM ===\n"); /* título */
    teste_entradas_invalidas();   /* T1 */
    teste_filtro_vazio();         /* T2 */
    teste_chave_vazia();          /* T3 */
    teste_exemplo_manual();       /* T4 */
    teste_repetidos();            /* T5 */
    teste_sem_falsos_negativos(); /* T6 */
    teste_busca_sem_sucesso();    /* T7 */
    teste_saturacao();            /* T8 */
    teste_parametros_otimos();    /* T9 */
    teste_phi();                  /* T10 */
    printf("TODOS OS %d TESTES PASSARAM\n", numero_teste); /* resumo */
    return 0;                                         /* sucesso */
}
