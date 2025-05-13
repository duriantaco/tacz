# Tacz 🔍 (Local-Only Version)

*Remember terminal commands using natural language with fully local LLMs*

![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)
![100% Local](https://img.shields.io/badge/privacy-100%25%20local-brightgreen)
![Ollama Compatible](https://img.shields.io/badge/Ollama-compatible-blue)
![PyPI version](https://img.shields.io/pypi/v/tacz)
![Python versions](https://img.shields.io/pypi/pyversions/tacz)

## 🚀 Features

- ✨ Fully local operation using Ollama
- 🧠 Smart command suggestions with explanations
- 🛡️ Enhanced safety checks for dangerous commands
- 📚 Command history and favorites
- ⚡ Cached responses for faster performance
- 🎯 Context-aware suggestions based on your environment
- 📝 Command editing before execution

## 📋 Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **RAM** | 8GB | 16GB+ |
| **Python** | 3.9+ | 3.11+ |
| **Disk Space** | 2GB free | 5GB+ free |
| **OS** | Windows 10+, macOS 10.14+, Linux | Any recent version |

Note: If you're using M1 chips or any older models, `llama` models will be slow

### Model Requirements

Different models have different memory requirements:

| Model | Size | RAM Required | Speed |
|-------|------|--------------|--------|
| `phi3:mini` | 1.8GB | 4GB | Fast ⚡ |
| `llama3.1:8b` | 4.7GB | 8GB | Balanced ⚖️ |
| `llama3.1:70b` | 40GB | 64GB | Slow but powerful 🧠 |

## 🔧 Installation

### Quick Install

1. Choose your AI engine

Pick one (Ollama is recommended):

##### ollama 
```bash
Ollama (Easy):

# macos
brew install ollama

# linux
curl -fsSL https://ollama.ai/install.sh | sh
```

##### llama.cpp

```bash
# Build from source
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make server
```

2. Start your ai engine

##### ollama 
```bash
# Terminal 1: Start server
ollama serve

# Terminal 2: Download model
ollama pull llama3.1:8b
```

#### for llama.cpp
```bash
# Download a model
curl -L -o model.gguf [HUGGINGFACE_MODEL_URL]

# Start server
./server -m model.gguf
```

### Install tacz

```bash
pip install tacz

tacz --setup
```

## 🎮 Usage

### Quick Start
```bash
# Direct query
tacz 'find all python files'

# Interactive mode
tacz

# Show command history
tacz --history

# Show favorite commands
tacz --favorites
```

## 🌟 Key Improvements

- **Everything runs locally** - No API keys, no internet required
- **Enhanced safety** - Multiple layers of dangerous command detection
- **Command history** - Track and search your commands
- **Favorites system** - Save your most-used commands
- **Better prompts** - Category-specific templates for better responses
- **Command editing** - Edit commands before execution
- **Database-powered storage** - Command history and preferences stored in SQLite

## ⚙️ Configuration

Edit `~/.taczrc` to customize:
```
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.1:8b
ENABLE_CACHE=true
CACHE_TTL_HOURS=24
ENABLE_HISTORY=true
ENABLE_SAFETY_CHECKS=true
```

## 🎯 Recommended Models

For best results:
- `llama3.1:8b` - Great balance of speed and accuracy
- `phi3:mini` - Faster, smaller model
- `mistral:latest` - More creative suggestions
- `codellama:7b` - Specialized for code and commands

## 🛡️ Safety Features

- Pattern matching for dangerous commands
- Command editing before execution
- Explicit warnings for risky operations
- Whitelist validation for basic commands
- Command history tracking

## 📝 Examples

```bash
# File operations
tacz 'show hidden files'
tacz 'delete empty directories recursively'

# System information
tacz 'check memory usage'
tacz 'find large files over 100MB'

# Git operations
tacz 'show git branches sorted by date'
tacz 'undo last commit but keep changes'

# Docker operations
tacz 'list running containers with exposed ports'
tacz 'clean up unused docker resources'
```

## 🤝 Contributing

Contributions welcome! This local-only version focuses on:
- Better prompt engineering
- Enhanced safety features
- Performance optimization
- User experience improvements

## 📄 License

Apache License 2.0 - See LICENSE file for details.