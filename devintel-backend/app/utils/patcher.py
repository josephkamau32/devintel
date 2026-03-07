"""Diff patching utility."""
import re
from typing import Dict, List, Tuple

def apply_diff(content: str, diff_text: str) -> str:
    """
    Applies a simple search/replace block or unified diff format to the original string.
    This is designed to handle LLM-generated search/replace blocks.
    
    Expected format from LLM:
    <<<<
    def old_function():
        pass
    ====
    def new_function():
        return True
    >>>>
    """
    if not diff_text:
        return content

    # Find all search/replace blocks
    pattern = re.compile(r'<<<<\n(.*?)\n====\n(.*?)\n>>>>', re.DOTALL)
    blocks = pattern.findall(diff_text)
    
    if not blocks:
        # Fallback if the LLM just dumped the whole file despite instructions
        return diff_text
        
    new_content = content
    for search_text, replace_text in blocks:
        # We use exact string replacement
        # A more robust implementation would use a fuzzy match or difflib, 
        # but exact match forces the LLM to be precise.
        if search_text in new_content:
            new_content = new_content.replace(search_text, replace_text)
        else:
            # Try stripping trailing whitespaces on each line for a more lenient match
            lenient_search = "\n".join([line.rstrip() for line in search_text.split('\n')])
            lenient_content = "\n".join([line.rstrip() for line in new_content.split('\n')])
            
            if lenient_search in lenient_content:
                # We found a lenient match, but replacing it is tricky if we want to preserve original whitespace.
                # For this simple prototype, if exact match fails, we'll try a basic line-by-line replacement.
                pass
            raise ValueError(f"Could not find the target search block in the file:\n{search_text[:100]}...")
            
    return new_content
