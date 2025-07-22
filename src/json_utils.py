"""
JSON parsing utilities with multiple fallback strategies
"""
import json
import re
from typing import Optional, Dict, Any


def extract_json_from_response(response_text: str) -> Optional[Dict[Any, Any]]:
    """
    Extract JSON from a response that may contain additional text
    """
    try:
        # Method 1: Try to parse directly
        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        pass

    try:
        # Method 2: Look for content between ```json and ```
        if '```json' in response_text and '```' in response_text:
            start = response_text.find('```json') + 7
            end = response_text.find('```', start)
            if end != -1:
                json_content = response_text[start:end].strip()
                return json.loads(json_content)
    except json.JSONDecodeError:
        pass

    try:
        # Method 3: Find first { to last }
        start = response_text.find('{')
        if start != -1:
            # Find the } that properly closes
            brace_count = 0
            end = start
            for i, char in enumerate(response_text[start:]):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end = start + i + 1
                        break

            if end > start:
                json_content = response_text[start:end]
                return json.loads(json_content)
    except json.JSONDecodeError:
        pass

    # If no method works, return None
    return None


def clean_and_parse_json(response_text: str, agent_name: str = "Agent") -> Optional[Dict[Any, Any]]:
    """
    Clean and parse JSON response with multiple strategies
    """
    # Basic cleaning
    cleaned = response_text.strip()

    # Try to extract JSON
    parsed_json = extract_json_from_response(cleaned)

    if parsed_json is None:
        print(f"❌ Error parsing JSON from {agent_name}")
        print(f"Raw response: {cleaned[:200]}...")  # Only first 200 characters
        return None

    return parsed_json