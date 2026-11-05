#include "../include/bloom.h" // Inclui o cabeçalho com as funções do Filtro de Bloom
#include <stdio.h>            // Inclui funções de entrada e saída (printf, fopen, fprintf, fclose)
#include <stdlib.h>           // Inclui funções padrão da linguagem
#include <string.h>           // Inclui funções de texto (strlen)
#include <math.h>             // Inclui funções matemáticas (sqrt, pow)

#define TOTAL_REPETICOES 30           // Define quantas vezes cada teste será repetido para tirar a média
#define TOTAL_CONSULTAS_NEGATIVAS 50000 // Define quantas chaves ausentes serão consultadas para medir o erro

// Estrutura para guardar a média e o desvio padrão dos resultados
typedef struct {
    double media;          // Valor médio das repetições
    double desvio_padrao;  // Desvio padrão das repetições
} Estatistica;

// Função que calcula a média e o desvio padrão de um vetor de números decimais
static Estatistica calcular_estatisticas(const double *valores, size_t quantidade) {
    double soma = 0.0;                                // Variável para somar todos os valores
    for (size_t i = 0; i < quantidade; i++) {         // Percorre todos os valores do vetor
        soma += valores[i];                           // Acumula o valor atual na soma
    }
    double media = soma / (double)quantidade;         // Divide a soma pela quantidade para achar a média

    double soma_diferencas_quadrado = 0.0;            // Variável para somar as diferenças ao quadrado
    for (size_t i = 0; i < quantidade; i++) {         // Percorre novamente todos os valores
        double diferenca = valores[i] - media;        // Calcula a distância do valor atual até a média
        soma_diferencas_quadrado += diferenca * diferenca; // Soma o quadrado dessa diferença
    }

    double variancia = 0.0;                           // Inicia a variância em zero
    if (quantidade > 1) {                             // Se houver mais de 1 elemento, calcula a variância amostral
        variancia = soma_diferencas_quadrado / (double)(quantidade - 1); // Divide por (quantidade - 1)
    }

    Estatistica resultado;                            // Cria a estrutura de retorno
    resultado.media = media;                          // Guarda a média calculada
    resultado.desvio_padrao = sqrt(variancia);        // Calcula a raiz quadrada da variância para ter o desvio padrão
    return resultado;                                 // Retorna as estatísticas prontas
}

// Função principal que executa o experimento comparando a teoria com a prática
int main(void) {
    const size_t lista_tamanhos[] = {10000, 50000, 250000}; // Lista de quantidades de elementos (n) testadas
    const size_t qtd_tamanhos = 3;                    // Quantidade de itens na lista de tamanhos

    const double lista_erros[] = {0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625}; // Taxas de erro alvo (P'') testadas
    const size_t qtd_erros = 6;                       // Quantidade de itens na lista de erros

    FILE *arquivo_csv = fopen("resultados_experimento.csv", "w"); // Abre o arquivo CSV para salvar os dados
    if (arquivo_csv == NULL) {                        // Verifica se deu erro ao criar o arquivo
        perror("Erro ao criar arquivo CSV");          // Mostra mensagem de erro no terminal
        return 1;                                     // Encerra o programa indicando erro
    }

    // Escreve a primeira linha (cabeçalho das colunas) no arquivo CSV
    fprintf(arquivo_csv, "n;P_alvo;N_bits;d_hashes;phi_teorico;phi_emp_media;phi_emp_sd;"
                         "P_emp_media;P_emp_sd;T_emp_media;T_emp_sd\n");

    printf("=========================================================================================\n"); // Linha divisória
    printf(" EXPERIMENTO: FILTRO DE BLOOM (1970) - COMPARACAO TEORICA VS. EMPIRICA\n"); // Título do experimento
    printf("=========================================================================================\n"); // Linha divisória

    for (size_t indice_tam = 0; indice_tam < qtd_tamanhos; indice_tam++) { // Percorre cada tamanho de conjunto (n)
        size_t qtd_elementos = lista_tamanhos[indice_tam]; // Pega a quantidade de elementos atual
        printf("\n>>> Executando bateria para n = %zu elementos...\n", qtd_elementos); // Informa o progresso na tela

        for (size_t indice_erro = 0; indice_erro < qtd_erros; indice_erro++) { // Percorre cada taxa de erro alvo
            double erro_alvo = lista_erros[indice_erro]; // Pega a taxa de erro (P'') atual

            double resultados_phi[TOTAL_REPETICOES];  // Vetor para guardar a proporção de bits 0 de cada repetição
            double resultados_erro[TOTAL_REPETICOES]; // Vetor para guardar a taxa de falsos positivos de cada repetição
            double resultados_tempo[TOTAL_REPETICOES]; // Vetor para guardar a média de bits lidos por rejeição

            BloomFilter *filtro_modelo = bloom_create_optimal(qtd_elementos, erro_alvo); // Cria um filtro para descobrir N'' e d
            size_t total_bits = filtro_modelo->total_bits; // Copia o total de bits ideal calculado
            size_t qtd_hashes = filtro_modelo->qtd_hashes; // Copia a quantidade de hashes ideal calculada
            bloom_destroy(filtro_modelo);             // Destrói o filtro modelo pois já pegamos os parâmetros

            for (size_t repeticao = 0; repeticao < TOTAL_REPETICOES; repeticao++) { // Repete o experimento 30 vezes
                BloomFilter *filtro = bloom_create(total_bits, qtd_hashes); // Cria um filtro novo e zerado
                char texto_chave[64];                 // Buffer para guardar o nome de cada chave gerada

                // Etapa 1: Inserir 'n' elementos diferentes no filtro
                for (size_t i = 0; i < qtd_elementos; i++) { // Laço para inserir todos os elementos
                    snprintf(texto_chave, sizeof(texto_chave), "inserido_%zu_%zu_%zu", indice_tam, repeticao, i); // Cria chave única
                    bloom_insert(filtro, texto_chave, strlen(texto_chave)); // Insere a chave no filtro
                }

                resultados_phi[repeticao] = bloom_empirical_phi(filtro); // Mede e guarda a proporção de bits que ficaram em 0

                // Etapa 2: Consultar elementos que NÃO foram inseridos para medir falsos positivos e bits lidos
                size_t qtd_falsos_positivos = 0;      // Contador de vezes que o filtro errou dizendo que a chave existia
                size_t soma_bits_nas_rejeicoes = 0;   // Soma de quantos bits foram olhados quando o filtro rejeitou a chave
                size_t qtd_rejeicoes = 0;             // Contador de vezes que o filtro acertou dizendo que a chave não existia

                for (size_t i = 0; i < TOTAL_CONSULTAS_NEGATIVAS; i++) { // Faz 50.000 buscas de elementos ausentes
                    snprintf(texto_chave, sizeof(texto_chave), "ausente_%zu_%zu_%zu", indice_tam, repeticao, i); // Cria chave não inserida
                    size_t bits_lidos = 0;            // Variável para receber quantos bits foram checados nesta busca
                    bool achou = bloom_query(filtro, texto_chave, strlen(texto_chave), &bits_lidos); // Consulta a chave ausente

                    if (achou) {                      // Se o filtro disse que encontrou uma chave que nunca foi inserida
                        qtd_falsos_positivos++;       // Conta mais um falso positivo
                    } else {                          // Se o filtro rejeitou corretamente a chave
                        soma_bits_nas_rejeicoes += bits_lidos; // Soma quantos bits precisou ler até achar o primeiro bit 0
                        qtd_rejeicoes++;              // Conta mais uma rejeição correta
                    }
                }

                // Calcula a taxa de falsos positivos dividindo os erros pelo total de buscas feitas
                resultados_erro[repeticao] = (double)qtd_falsos_positivos / (double)TOTAL_CONSULTAS_NEGATIVAS;

                // Calcula quantos bits em média foram lidos até rejeitar uma chave (esperado ser ~2.0 no ponto ótimo)
                if (qtd_rejeicoes > 0) {              // Evita divisão por zero caso todas as buscas deem falso positivo
                    resultados_tempo[repeticao] = (double)soma_bits_nas_rejeicoes / (double)qtd_rejeicoes; // Média de bits por rejeição
                } else {                              // Caso não tenha havido nenhuma rejeição
                    resultados_tempo[repeticao] = 0.0; // Define a média como zero
                }

                bloom_destroy(filtro);                // Libera a memória do filtro usado nesta repetição
            }

            Estatistica est_phi = calcular_estatisticas(resultados_phi, TOTAL_REPETICOES);     // Calcula média e desvio de phi
            Estatistica est_erro = calcular_estatisticas(resultados_erro, TOTAL_REPETICOES);   // Calcula média e desvio do erro P''
            Estatistica est_tempo = calcular_estatisticas(resultados_tempo, TOTAL_REPETICOES); // Calcula média e desvio de T''

            // Calcula o valor teórico esperado para a proporção de bits zero: (1 - d / N'')^n
            double phi_teorico = pow(1.0 - ((double)qtd_hashes / (double)total_bits), (double)qtd_elementos);

            // Salva a linha com todos os resultados calculados dentro do arquivo CSV
            fprintf(arquivo_csv, "%zu;%.6f;%zu;%zu;%.4f;%.4f;%.4f;%.4f;%.4f;%.4f;%.4f\n",
                    qtd_elementos, erro_alvo, total_bits, qtd_hashes, phi_teorico,
                    est_phi.media, est_phi.desvio_padrao,
                    est_erro.media, est_erro.desvio_padrao,
                    est_tempo.media, est_tempo.desvio_padrao);

            // Mostra o resumo dos resultados no terminal para acompanhamento
            printf("  P alvo: %6.4f | Bits: %8zu | d: %2zu | phi: %.3f (teor: %.3f) | P emp: %.4f +- %.4f | T emp: %.2f +- %.2f\n",
                   erro_alvo, total_bits, qtd_hashes, est_phi.media, phi_teorico,
                   est_erro.media, est_erro.desvio_padrao, est_tempo.media, est_tempo.desvio_padrao);
        }
    }

    fclose(arquivo_csv);                              // Fecha e salva o arquivo CSV no disco
    printf("\nExperimento concluido com sucesso! Arquivo 'resultados_experimento.csv' gerado.\n"); // Mensagem final
    return 0;                                         // Encerra o programa com sucesso
}
