#!/usr/bin/env python3
import json
import re
import requests
from pathlib import Path

def get_llm_tags(content: str) -> list[str]:
    """Get tags from local LLM"""
    prompt = f"Generate 3-5 tags for this note. Return only JSON array: ['tag1', 'tag2']. Content: {content[:400]}..."
    
    payload = {
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 50}
    }
    
    try:
        response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=20)
        result = response.json()
        llm_text = result["response"]
        
        # Extract JSON array
        match = re.search(r'\[.*?\]', llm_text)
        if match:
            return json.loads(match.group())
        return []
    except Exception as e:
        print(f"LLM error: {e}")
        return []

def add_tags_to_file(file_path: Path):
    """Add LLM-generated tags to a markdown file"""
    content = file_path.read_text()
    
    # Skip if already has frontmatter with tags
    if content.startswith("---") and "tags:" in content[:200]:
        print(f"Skipping {file_path.name} - already has tags")
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
    print(f"Getting tags for {file_path.name}...")
    tags = get_llm_tags(main_content)
    
    if tags:
        print(f"  Tags: {tags}")
        # Add frontmatter with tags
        frontmatter = "---\ntags:\n" + "\n".join([f"- {tag}" for tag in tags]) + "\n---\n\n"
        new_content = frontmatter + main_content
        
        file_path.write_text(new_content)
        print(f"  Updated {file_path.name}")
    else:
        print(f"  No tags generated for {file_path.name}")

def main():
    vault_dir = Path("obsidian_vault")
    md_files = list(vault_dir.glob("*.md"))
    
    print(f"Found {len(md_files)} markdown files")
    
    for file_path in md_files:
        add_tags_to_file(file_path)
        print()

if __name__ == "__main__":
    main()