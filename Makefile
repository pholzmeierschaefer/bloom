CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -O2 -D_POSIX_C_SOURCE=200809L -Iinclude
LIBS = -lm

all: bin/teste_corretude bin/exemplo bin/experimento

bin/%: tests/%.c src/filtro_bloom.c include/filtro_bloom.h
	mkdir -p bin
	$(CC) $(CFLAGS) tests/$*.c src/filtro_bloom.c -o $@ $(LIBS)

# Roda os testes de correção
teste: bin/teste_corretude
	./bin/teste_corretude

# Mostra o exemplo passo a passo
exemplo: bin/exemplo
	./bin/exemplo

# Roda o experimento (gera resultados/*.csv; leva alguns minutos)
experimento: bin/experimento
	mkdir -p resultados
	./bin/experimento

# Roda os testes com detector de erros de memória (AddressSanitizer + UBSan)
memoria:
	mkdir -p bin
	$(CC) $(CFLAGS) -g -fsanitize=address,undefined tests/teste_corretude.c src/filtro_bloom.c -o bin/teste_memoria $(LIBS)
	./bin/teste_memoria

# Gera os PDFs (relatório, testes e roteiro dos slides) em docs/
pdfs:
	python3 docs/gerar_pdfs.py

limpar:
	rm -rf bin

.PHONY: all teste exemplo experimento memoria pdfs limpar
