#!/usr/bin/env python3

import re
from pathlib import Path

def remove_frontmatter_tags(file_path: Path):
    """Remove YAML frontmatter from markdown files safely"""
    content = file_path.read_text(encoding='utf-8')
    
    # Pattern to match YAML frontmatter at the beginning of file
    frontmatter_pattern = r'^---\n.*?\n---\n\n?'
    
    # Remove frontmatter if it exists
    cleaned_content = re.sub(frontmatter_pattern, '', content, flags=re.DOTALL)
    
    # Write back the cleaned content
    file_path.write_text(cleaned_content, encoding='utf-8')
    print(f"Removed tags from: {file_path.name}")

def main():
    vault_dir = Path("obsidian_vault")
    md_files = list(vault_dir.glob("*.md"))
    
    print(f"Removing tags from {len(md_files)} markdown files...")
    
    for file_path in md_files:
        remove_frontmatter_tags(file_path)
    
    print("Done!")

if __name__ == "__main__":
    main()