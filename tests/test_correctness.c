#include "../include/bloom.h" // Inclui o cabeçalho com as funções do Filtro de Bloom
#include <stdio.h>            // Inclui funções de entrada e saída (printf, snprintf)
#include <string.h>           // Inclui funções de manipulação de texto (strlen)
#include <assert.h>           // Inclui a macro assert para validar os testes automaticamente

// Teste 1: Verifica se o filtro lida corretamente com valores inválidos sem travar
void testar_entradas_invalidas(void) {
    printf("[1/5] Testando casos-limite e entradas invalidas...\n"); // Exibe mensagem de início do teste 1
    assert(bloom_create(0, 5) == NULL);               // Garante que criar com 0 bits retorna NULL
    assert(bloom_create(100, 0) == NULL);             // Garante que criar com 0 hashes retorna NULL
    assert(bloom_create_optimal(0, 0.05) == NULL);    // Garante que criar com 0 elementos esperados retorna NULL
    assert(bloom_create_optimal(100, 0.0) == NULL);   // Garante que criar com erro 0% retorna NULL
    assert(bloom_create_optimal(100, 1.0) == NULL);   // Garante que criar com erro 100% retorna NULL

    BloomFilter *filtro = bloom_create(100, 3);       // Cria um filtro válido de 100 bits e 3 hashes
    assert(filtro != NULL);                           // Confirma que o filtro foi criado com sucesso
    assert(!bloom_insert(filtro, NULL, 5));           // Garante que inserir ponteiro nulo falha com segurança
    assert(!bloom_insert(filtro, "teste", 0));        // Garante que inserir tamanho zero falha com segurança
    assert(!bloom_query(filtro, NULL, 5, NULL));      // Garante que consultar ponteiro nulo retorna falso
    assert(!bloom_query(filtro, "teste", 0, NULL));   // Garante que consultar tamanho zero retorna falso

    bloom_destroy(filtro);                            // Libera a memória do filtro criado
    bloom_destroy(NULL);                              // Garante que destruir um ponteiro nulo não causa erro
    printf("      OK!\n");                            // Informa que o teste 1 passou
}

// Teste 2: Verifica o comportamento de um filtro recém-criado (totalmente vazio)
void testar_filtro_vazio(void) {
    printf("[2/5] Testando filtro vazio...\n");       // Exibe mensagem de início do teste 2
    BloomFilter *filtro = bloom_create(1000, 4);      // Cria um filtro de 1000 bits e 4 hashes
    assert(filtro != NULL);                           // Confirma que o filtro foi alocado corretamente

    size_t bits_testados = 0;                         // Variável para guardar quantos bits serão lidos na busca
    bool encontrado = bloom_query(filtro, "inexistente", 11, &bits_testados); // Busca uma palavra no filtro vazio
    assert(!encontrado);                              // Garante que o elemento não foi encontrado
    assert(bits_testados == 1);                       // Garante que parou logo no 1º bit (pois já estava em 0)
    assert(bloom_empirical_phi(filtro) == 1.0);       // Garante que 100% (1.0) dos bits estão valendo 0

    bloom_destroy(filtro);                            // Libera a memória do filtro
    printf("      OK!\n");                            // Informa que o teste 2 passou
}

// Teste 3: Verifica que o filtro NUNCA dá falso negativo (tudo que é inserido é encontrado)
void testar_ausencia_falsos_negativos(void) {
    printf("[3/5] Testando ausencia de falsos negativos...\n"); // Exibe mensagem de início do teste 3
    const size_t quantidade_elementos = 1000;         // Define que vamos testar com 1000 elementos
    BloomFilter *filtro = bloom_create_optimal(quantidade_elementos, 0.01); // Cria filtro ótimo para 1% de erro
    assert(filtro != NULL);                           // Confirma que o filtro foi criado

    char texto_chave[64];                             // Buffer de texto para montar o nome de cada chave
    for (size_t i = 0; i < quantidade_elementos; i++) { // Laço para inserir as 1000 chaves diferentes
        snprintf(texto_chave, sizeof(texto_chave), "chave_uffs_%zu", i); // Gera um texto único (ex: "chave_uffs_0")
        assert(bloom_insert(filtro, texto_chave, strlen(texto_chave))); // Insere a chave e confirma que deu certo
    }

    for (size_t i = 0; i < quantidade_elementos; i++) { // Laço para buscar todas as 1000 chaves inseridas
        snprintf(texto_chave, sizeof(texto_chave), "chave_uffs_%zu", i); // Recria o mesmo texto da chave
        assert(bloom_query(filtro, texto_chave, strlen(texto_chave), NULL) == true); // Garante que a busca retorna verdadeiro
    }

    bloom_destroy(filtro);                            // Libera a memória do filtro
    printf("      OK!\n");                            // Informa que o teste 3 passou
}

// Teste 4: Verifica se inserir o mesmo elemento várias vezes não liga bits extras
void testar_insercoes_duplicadas(void) {
    printf("[4/5] Testando insercao de elementos duplicados...\n"); // Exibe mensagem de início do teste 4
    BloomFilter *filtro = bloom_create(500, 4);       // Cria um filtro de 500 bits e 4 hashes
    assert(filtro != NULL);                           // Confirma que o filtro foi criado

    const char *chave_repetida = "elemento_repetido"; // Define o texto que será inserido várias vezes
    bloom_insert(filtro, chave_repetida, strlen(chave_repetida)); // Insere a chave pela primeira vez
    double proporcao_zeros_inicial = bloom_empirical_phi(filtro); // Mede a proporção de bits 0 após a 1ª inserção

    for (int i = 0; i < 50; i++) {                    // Repete a inserção da mesma chave mais 50 vezes
        bloom_insert(filtro, chave_repetida, strlen(chave_repetida)); // Insere exatamente o mesmo texto
    }
    double proporcao_zeros_final = bloom_empirical_phi(filtro); // Mede novamente a proporção de bits 0

    assert(proporcao_zeros_inicial == proporcao_zeros_final); // Garante que nenhum bit novo foi alterado nas repetições

    bloom_destroy(filtro);                            // Libera a memória do filtro
    printf("      OK!\n");                            // Informa que o teste 4 passou
}

// Teste 5: Verifica se um filtro muito pequeno enche (satura) e passa a gerar falsos positivos
void testar_saturacao_do_filtro(void) {
    printf("[5/5] Testando saturacao do filtro...\n"); // Exibe mensagem de início do teste 5
    BloomFilter *filtro = bloom_create(32, 3);        // Cria um filtro minúsculo de apenas 32 bits
    assert(filtro != NULL);                           // Confirma que o filtro foi criado

    char texto_chave[32];                             // Buffer para gerar os nomes dos itens
    for (size_t i = 0; i < 200; i++) {                // Insere 200 itens diferentes para encher os 32 bits
        snprintf(texto_chave, sizeof(texto_chave), "item_%zu", i); // Formata o nome do item atual
        bloom_insert(filtro, texto_chave, strlen(texto_chave)); // Insere o item no filtro
    }

    assert(bloom_empirical_phi(filtro) < 0.05);       // Garante que sobraram menos de 5% de bits valendo 0
    assert(bloom_query(filtro, "fora_do_conjunto", 16, NULL) == true); // Confirma que ocorre falso positivo com o filtro cheio

    bloom_destroy(filtro);                            // Libera a memória do filtro
    printf("      OK!\n");                            // Informa que o teste 5 passou
}

// Função principal que executa todos os 5 testes em sequência
int main(void) {
    printf("=== EXECUTANDO TESTES DE CORRECAO (FILTRO DE BLOOM) ===\n"); // Cabeçalho dos testes
    testar_entradas_invalidas();                      // Executa o teste 1
    testar_filtro_vazio();                            // Executa o teste 2
    testar_ausencia_falsos_negativos();               // Executa o teste 3
    testar_insercoes_duplicadas();                    // Executa o teste 4
    testar_saturacao_do_filtro();                     // Executa o teste 5
    printf("Todos os testes passaram com sucesso!\n"); // Mensagem final de sucesso
    return 0;                                         // Encerra o programa sem erros
}
