import requests
import json

# Test LLM connection
def test_llm():
    url = "http://localhost:11434/api/generate"
    
    payload = {
        "model": "llama3.2",
        "prompt": "Generate 3 tags for a note about machine learning. Return only a JSON array like [\"tag1\", \"tag2\", \"tag3\"]",
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 50,
        }
    }
    
    try:
        print("Testing LLM connection...")
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        print(f"Response: {result}")
        
        llm_response = result.get("response", "").strip()
        print(f"LLM output: {llm_response}")
        
        # Try to parse JSON
        import re
        json_match = re.search(r'\[.*?\]', llm_response, re.DOTALL)
        if json_match:
            tags = json.loads(json_match.group())
            print(f"Extracted tags: {tags}")
        else:
            print("No JSON array found in response")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_llm()