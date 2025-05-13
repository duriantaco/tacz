# Tacz Installation Guide

## Prerequisites

- Python 3.9 or higher
- macOS, Linux, or Windows
- Terminal/Command Prompt access

## Quick Start (Recommended)

### 1. Install Ollama

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download from [ollama.ai/download](https://ollama.ai/download)

### 2. Start Ollama and Download Model

```bash
# Terminal 1: Start server
ollama serve

# Terminal 2: Download model
ollama pull llama3.1:8b
```

### 3. Install Tacz

```bash
pip install tacz
```

### 4. Configure

```bash
tacz --setup
```

Select "Ollama" as provider, keep default settings.

## Alternative Installation: llama.cpp

For advanced users who want a lightweight option:

### 1. Build llama.cpp

```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make server
```

### 2. Download a Model

```bash
# eg: download Llama 3 8B
curl -L -o llama-3-8b.gguf https://huggingface.co/Meta-Llama-3-8B-Instruct-GGUF/resolve/main/Meta-Llama-3-8B-Instruct.Q4_K_M.gguf
```

### 3. Start Server

```bash
./server -m llama-3-8b.gguf -c 2048
```

### 4. Install and Configure Tacz

```bash
pip install tacz
tacz --setup
```

Select "llama.cpp server" as provider.

## First Run

Test your installation:

```bash
tacz "list files"
```

You should see command suggestions!

## Troubleshooting

### Ollama Issues

**"Failed to connect"**
- Make sure `ollama serve` is running
- Try: `curl http://localhost:11434`

**"Model not found"**
- Pull the model: `ollama pull llama3.1:8b`
- List available: `ollama list`

### llama.cpp Issues

**"Connection refused"**
- Ensure server is running: `./server -m model.gguf`
- Check port: default is 8080

### General Issues

**"Command not found: tacz"**
- Reinstall: `pip install --force-reinstall tacz`
- Check PATH: `which tacz`

**"No module named tacz"**
- Update pip: `pip install --upgrade pip`
- Try: `python -m pip install tacz`

## Configuration Options

Edit `~/.taczrc` for custom settings:

```ini
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.1:8b
ENABLE_CACHE=true
CACHE_TTL_HOURS=24
ENABLE_HISTORY=true
ENABLE_SAFETY_CHECKS=true
```

## Upgrading

```bash
pip install --upgrade tacz
```

## Uninstalling

```bash
pip uninstall tacz
rm -f ~/.taczrc
rm -f ~/.tacz_cache.json
rm -f ~/.tacz_history.json
rm -f ~/.tacz_favorites.json
```

## Development Installation

For contributing:

```bash
git clone https://github.com/your-repo/tacz
cd tacz
pip install -e .
```

## Need Help?

- GitHub Issues: [github.com/duriantaco/tacz/issues](https://github.com/duriantaco/tacz/issues)

---

*Last updated: $(date)*