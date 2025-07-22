"""
Prompt templates for metaphor analysis agents
"""
import json
from typing import List, Dict

# Filter examples for Agent 2
FILTER_EXAMPLES = {
    'valid': """
VALID METAPHORS (physical domain → financial domain):

• "fire sales" → FIRE (consumes quickly, destructive) → SALES (quick, destroy value)
• "weather a downturn" → CLIMATE/STORM (resist natural elements) → CRISIS (resist economic difficulties)
• "tangled and opaque picture" → TANGLED PHYSICAL OBJECT → COMPLEX MARKET
• "hub-and-spoke network" → PHYSICAL WHEEL (center and spokes) → MARKET STRUCTURE
• "feedback loop" → MECHANICAL SYSTEM (closed circuit) → ECONOMIC SYSTEM
• "adverse feedback loop" → UNCONTROLLED MACHINE → PROBLEMATIC ECONOMIC SYSTEM
• "buildup of risk" → PHYSICAL CONSTRUCTION/ACCUMULATION → RISK ACCUMULATION
• "near collapse" → PHYSICAL STRUCTURE FALLING → FINANCIAL SYSTEM FAILING
""",

    'invalid': """
INVALID EXPRESSIONS (reject these types):

• "take stock" → common idiomatic expression, no systematic conceptual mapping
• "move forward" → very common, no specific source domain
• "area of interest" → standard language, not metaphorical
• "market participants" → normal technical terminology
• "financial institutions" → sector terminology
• "regulatory framework" → technical concept, not metaphor
• "liquidity provision" → standard financial terminology
• "access to capital" → normal technical language
• "under the right circumstances" → common expression
• "significant current interest" → standard language
• "make progress" → very common expression
• "address issues" → technical terminology
"""
}


def create_candidate_prompt(text: str) -> str:
    """Agent 1: Uses proven prompt with Gemini 2.0"""
    base_text = f"Analyze the following text:\n\n{text}"

    return f"""{base_text}

You are a linguistics expert who identifies ONLY very specific conceptual metaphors.

STRICT RULE: Only find metaphors that EXPLICITLY map physical/concrete concepts to financial/abstract concepts.

MANDATORY CRITERIA for a valid metaphor:
1. Must use vocabulary from a physical/concrete domain (weather, construction, machines, fire, etc.)
2. Must apply that vocabulary to abstract financial/economic concepts
3. Must create a systematic conceptual mapping

EXAMPLES of VALID metaphors of the type you're looking for:
- "fire sales" (FIRE → quick/destructive sales)
- "weather a downturn" (WEATHER → resist crisis)
- "feedback loop" (MACHINE → economic system)
- "tangled picture" (TANGLED PHYSICAL OBJECT → complex market)
- "hub-and-spoke network" (PHYSICAL WHEEL → market structure)

ABSOLUTE EXCLUSIONS (DO NOT include):
- "build up", "take stock", "move forward" (too common)
- "financial institutions", "market participants" (normal technical language)
- "regulatory framework", "oversight" (specialized terminology)
- "access to capital", "liquidity provision" (standard financial concepts)
- Any phrase that is standard financial terminology

FINAL INSTRUCTION: If you find more than 5 metaphors, you're being too permissive. Only the most obvious and clear ones.

Respond in JSON format:
{{
    "candidates": [
        {{
            "text": "exact metaphor text",
            "context": "complete context where it appears"
        }}
    ]
}}
"""


def create_filter_prompt(candidates: List[Dict], examples: Dict = FILTER_EXAMPLES) -> str:
    """Agent 2: Filters candidates using strict criteria"""
    candidates_text = json.dumps(candidates, indent=2, ensure_ascii=False)

    return f"""YOU ARE AGENT 2: EXPERT FILTER FOR CONCEPTUAL METAPHORS

Agent 1 (Gemini 2.0) identified these candidates:
{candidates_text}

YOUR MISSION: Filter and keep ONLY true conceptual metaphors.

STRICT APPROVAL CRITERIA:
1. Must map a specific PHYSICAL/CONCRETE domain to an ABSTRACT/FINANCIAL one
2. The mapping must be SYSTEMATIC and STRUCTURAL (not decorative)
3. Must use specific vocabulary from the source domain (weather, fire, machines, construction, etc.)

VALID EXAMPLES (APPROVE these types):
{examples['valid']}

INVALID EXAMPLES (REJECT these types):
{examples['invalid']}

FILTERING INSTRUCTIONS:
- Only approve candidates clearly similar to the valid examples
- If you have doubts about a candidate, REJECT IT
- Maximum 5 approved metaphors (if more, take the clearest ones)

SIMPLIFIED RESPONSE FORMAT:
{{
    "metaphors": [
        {{
            "text": "approved metaphor",
            "context": "complete context where it appears"
        }}
    ]
}}
"""