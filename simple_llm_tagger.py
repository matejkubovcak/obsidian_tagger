#!/usr/bin/env python3
import json
import re
import requests
import logging
from pathlib import Path
from datetime import datetime

# Load configuration
def load_config():
    """Load configuration from JSON file"""
    config_path = Path(__file__).parent / "config.json"
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {config_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {e}")

# Load config at module level
config = load_config()

# Set up logging
def setup_logging():
    """Set up logging to both console and file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"llm_tagger_{timestamp}.log"
    
    # Create logger
    logger = logging.getLogger('llm_tagger')
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# Initialize logger
logger = setup_logging()

def get_llm_tags(content: str) -> list[str]:
    """Get tags from local LLM"""
    # Truncate content to configured length
    truncated_content = content[:config["content_length_limit"]]
    prompt = config["prompt_template"].format(content=truncated_content)
    
    payload = {
        "model": config["model"],
        "prompt": prompt,
        "stream": config["stream"],
        "options": config["options"]
    }
    
    try:
        response = requests.post(config["api_url"], json=payload, timeout=config["timeout"])
        result = response.json()
        llm_text = result["response"]
        logger.info(f"LLM response: {llm_text}")
        
        # Extract JSON array
        match = re.search(r'\[.*?\]', llm_text)
        if match:
            return json.loads(match.group())
        return []
    except Exception as e:
        logger.error(f"LLM error: {e}")
        return []

def add_tags_to_file(file_path: Path):
    """Add LLM-generated tags to a markdown file"""
    content = file_path.read_text()
    
    # Skip if already has frontmatter with tags
    if content.startswith("---") and "tags:" in content[:200]:
        logger.info(f"Skipping {file_path.name} - already has tags")
        return
    
    # Get content without any existing frontmatter
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            main_content = content[end+3:].strip()
        else:
            main_content = content
    else:
        main_content = content
    
    # Get LLM tags
    logger.info(f"Getting tags for {file_path.name}...")
    tags = get_llm_tags(main_content)
    
    if tags:
        logger.info(f"  Tags: {tags}")
        # Add frontmatter with tags
        frontmatter = "---\ntags:\n" + "\n".join([f"- {tag}" for tag in tags]) + "\n---\n\n"
        new_content = frontmatter + main_content
        
        file_path.write_text(new_content)
        logger.info(f"  Updated {file_path.name}")
    else:
        logger.info(f"  No tags generated for {file_path.name}")

def main():
    vault_dir = Path("obsidian_vault")
    md_files = list(vault_dir.glob("*.md"))
    
    logger.info(f"Found {len(md_files)} markdown files")
    
    for file_path in md_files:
        add_tags_to_file(file_path)
        logger.info("")  # Empty line for readability

if __name__ == "__main__":
    main()
