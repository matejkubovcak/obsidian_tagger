# Local note tagging service for Obsidian Vaults
This project aims to add tags to unstructured obsidian notes in a completely local and secure way by utilizing the ollama llm server.


## Quick Start

1. **Install Ollama** (if not already installed):
   ```bash
   # macOS
   brew install ollama
   
   # Start Ollama service(or run the app via gui)
   ollama serve
   ```

2. **Pull a model**:
   ```bash
   # Recommended models:
   ollama pull llama3.2        # Fast, good quality - default
   ollama pull mistral         # Alternative option, make sure to specify this in the config 
   ```

3. **Run the script**:
   ```bash
   python simple_llm_tagger.py
   ```


you can leave ollama serve running in a background, it's a lightweight http server - only loading the models into memory per request

## Automated usage
Run 'run.py' for automated startup and shutdown of the ollama service. 



