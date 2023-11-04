CXX = g++
CXXFLAGS = -std=c++17

# Source directory
SRC_DIR = src

# Output directory for compiled executables
BIN_DIR = bin

# Find all C++ source files recursively in subdirectories
SOURCES := $(shell find $(SRC_DIR) -type f -name "*.cpp")

# Create a list of corresponding output file names
EXECUTABLES := $(patsubst $(SRC_DIR)/%.cpp, $(BIN_DIR)/%, $(SOURCES))

# Default target to build all executables
all: $(EXECUTABLES)

# Rule to compile C++ source files into executables
$(BIN_DIR)/%: $(SRC_DIR)/%.cpp
	@mkdir -p $(@D)
	$(CXX) $(CXXFLAGS) $< -o $@

# Clean up the compiled executables
clean:
	rm -rf $(BIN_DIR)

# Run the main file
run-main:
	./bin/main

.PHONY: all clean
