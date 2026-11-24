# Filtro de Bloom (Método 2 – Bloom, 1970)

**Disciplina:** Estruturas de Dados II (GEX1210) – UFFS Campus Chapecó
**Artigo:** Bloom, B. H. (1970). *Space/time trade-offs in hash coding with allowable errors*. Communications of the ACM, 13(7), 422–426.

## Integrantes
| Nome | Matrícula |
|---|---|
| Giovanni Timonez | ____ |
| Pedro Henrique Holzmeier Schaefer | ____ |
| Rafael Knebel | ____ |
| Verônica Martini | ____ |
| Vitor Lago | ____ |

## O que é
Estrutura que responde "esta mensagem pertence ao conjunto?" usando só um vetor de bits e `d` funções de hash.
Aceita uma taxa pequena de **falsos positivos** e **nunca** produz falso negativo.

## Dependências
- `gcc` com suporte a C11 e `make`
- biblioteca matemática (`-lm`, já incluída no Makefile)
- só para regenerar os PDFs: `python3` com `pycairo`

## Como compilar, executar e testar
```bash
make               # compila tudo (pasta bin/)
make teste         # 10 testes de correção
make memoria       # os mesmos testes com AddressSanitizer + UBSan
make exemplo       # exemplo passo a passo (24 bits, 3 hashes)
make experimento   # experimento completo -> resultados/*.csv (alguns segundos)
make pdfs          # regenera docs/relatorio.pdf, docs/testes.pdf e docs/slides.pdf
make limpar        # apaga bin/
```

## Estrutura
| Arquivo | Conteúdo |
|---|---|
| `include/filtro_bloom.h` | interface do filtro, invariantes e correspondência com o artigo |
| `src/filtro_bloom.c` | implementação (cada linha comentada) |
| `tests/teste_corretude.c` | 10 testes automatizados (entradas inválidas, filtro vazio, repetidos, sem falso negativo, saturação…) |
| `tests/exemplo.c` | exemplo passo a passo usado nos slides |
| `tests/experimento.c` | experimento: φ'', P'', T'', espaço e tempo × fórmulas do artigo; caso da hifenização |
| `resultados/` | CSVs do experimento e saídas dos testes |
| `docs/relatorio.pdf` | relatório técnico (3 páginas + referências) |
| `docs/testes.pdf` | relatório de testes e experimento |
| `docs/slides.pdf` | roteiro dos slides do seminário (um slide por página, com notas de fala) |
| `docs/*.py` | scripts que geram os PDFs a partir dos resultados reais |

## Correspondência com o artigo
| Artigo | Código |
|---|---|
| N'' (bits) | `total_bits` |
| d (endereços por mensagem) | `quantidade_hashes` |
| n (mensagens inseridas) | `quantidade_inseridos` |
| φ'' = (1 − d/N'')ⁿ | `filtro_phi_empirico` (medido) e `filtro_phi_teorico` (fórmula) |
| P'' = (1 − φ'')^d | `filtro_erro_teorico` |
| T'' (bits lidos até rejeitar) | argumento `bits_lidos` de `filtro_consultar` |
| ponto ótimo φ'' = 1/2 | `filtro_criar_otimo` (d = ⌈log₂(1/P'')⌉, N'' ≈ 1,44·n·log₂(1/P'')) |

## Simplificações e limitações
- Os `d` endereços saem de **dois hashes** (FNV-1a e DJB2) combinados (`h1 + i·passo`), não de `d` funções independentes; os endereços de uma chave podem coincidir.
- Chaves são textos terminados em `'\0'` (a chave vazia `""` é válida; `NULL` é inválida).
- O Método 1 do artigo não foi implementado (só comparado pelas fórmulas). Não há remoção de chaves.
- O "dicionário em disco" da hifenização é simulado: contamos como acesso ao disco cada consulta aceita.
- Hashes não criptográficos: não resistem a um adversário.
- Tempo medido depende da máquina e do cache e não comprova complexidade assintótica.

## Uso de IA
Um assistente de IA foi usado, a pedido do grupo, para redigir/simplificar o código, os testes, o experimento e os PDFs.
Os testes e o experimento foram executados e os resultados conferidos contra as fórmulas do artigo.
