CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -O2 -Iinclude
LDFLAGS = -lm

SRC_DIR = src
TEST_DIR = tests
BIN_DIR = bin
BUILD_DIR = build

OBJS = $(BUILD_DIR)/bloom.o

all: $(BIN_DIR)/test_correctness $(BIN_DIR)/experiment

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

$(BUILD_DIR)/bloom.o: $(SRC_DIR)/bloom.c include/bloom.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -c $(SRC_DIR)/bloom.c -o $@

$(BIN_DIR)/test_correctness: $(TEST_DIR)/test_correctness.c $(OBJS) | $(BIN_DIR)
	$(CC) $(CFLAGS) $< $(OBJS) -o $@ $(LDFLAGS)

$(BIN_DIR)/experiment: $(TEST_DIR)/experiment.c $(OBJS) | $(BIN_DIR)
	$(CC) $(CFLAGS) $< $(OBJS) -o $@ $(LDFLAGS)

test: $(BIN_DIR)/test_correctness
	./$(BIN_DIR)/test_correctness

run_experiment: $(BIN_DIR)/experiment
	./$(BIN_DIR)/experiment

clean:
	rm -rf $(BUILD_DIR) $(BIN_DIR) resultados_experimento.csv

.PHONY: all test run_experiment clean