# LLM-Based Tagging Setup

## Quick Start

1. **Install Ollama** (if not already installed):
   ```bash
   # macOS
   brew install ollama
   
   # Start Ollama service
   ollama serve
   ```

2. **Pull a model**:
   ```bash
   # Recommended models:
   ollama pull llama3.2        # Fast, good quality
   ollama pull mistral         # Alternative option
   ollama pull codellama       # For code-heavy notes
   ```

3. **Run the script**:
   ```bash
   python tag_vault_llm.py
   ```

## Configuration

Edit `LLM_CONFIG` in `tag_vault_llm.py`:

```python
LLM_CONFIG = {
    "url": "http://localhost:11434/api/generate",  # Ollama default
    "model": "llama3.2",  # Change to your model
    "temperature": 0.3,   # Lower = more consistent
}
```

## Alternative LLM Providers

### OpenAI-compatible APIs (LocalAI, text-generation-webui)
- Change URL to your local endpoint
- May need API key header

### LM Studio
- Default: `http://localhost:1234/v1/chat/completions`
- Different API format (modify the query function)

## Features

- Intelligent content analysis
- Hierarchical tagging (e.g., `tech/python`)
- Preserves existing tags
- JSON-based tag extraction
- Error handling for LLM failures