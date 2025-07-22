"""
Main metaphor analysis system with two-agent pipeline
"""
import time
from typing import Dict, List, Optional, Any
from .gemini_client import GeminiClient
from .prompt_templates import create_candidate_prompt, create_filter_prompt
from .json_utils import clean_and_parse_json


class MetaphorAnalyzer:
    """Two-agent system for conceptual metaphor analysis"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the metaphor analyzer
        
        Args:
            api_key: Google API key (if None, will get from environment)
        """
        self.client = GeminiClient(api_key)
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Complete two-agent analysis system for metaphor detection
        
        Agent 1 (Gemini 2.0): Initial detection - more sensitive
        Agent 2 (Gemini 2.5): Rigorous validation - more precise
        
        Args:
            text: Text to analyze for metaphors
            
        Returns:
            Dict with analysis results
        """
        print("=" * 60)
        print("🔍 TWO-AGENT SYSTEM - METAPHOR ANALYSIS")
        print("=" * 60)
        
        # ================= AGENT 1: DETECTION =================
        print("\n🤖 AGENT 1 (Gemini 2.0): Detecting candidates...")
        print("-" * 50)
        
        try:
            # Request with specific rate limit control for Gemini 2.0
            response1 = self.client.safe_gemini_request(
                self.client.agent1_model, 
                create_candidate_prompt(text), 
                "Agent 1", 
                "gemini-2.0-flash"
            )
            result1 = response1.text.strip()
            
            # Clean JSON response
            candidates_data = clean_and_parse_json(result1, "Agent 1")
            if candidates_data is None:
                return {"success": False, "error": "Agent 1 JSON parsing failed"}
            
            candidates = candidates_data.get('candidates', [])
            
            print(f"✅ Candidates detected: {len(candidates)}")
            if candidates:
                print("\n📝 Candidate list:")
                for i, candidate in enumerate(candidates, 1):
                    print(f"   {i}. '{candidate['text']}'")
                    
        except Exception as e:
            print(f"❌ Error in Agent 1: {e}")
            return {"success": False, "error": f"Agent 1 error: {str(e)}"}
        
        if not candidates:
            print("⚠️  No candidates found. Ending analysis.")
            return {
                "candidates": [], 
                "final_metaphors": [], 
                "agent1_count": 0, 
                "agent2_count": 0,
                "success": True
            }
        
        # Intelligent pause based on combined limits
        usage = self.client.get_usage_summary()
        pause_time = max(6, 60 - usage['combined']['rpm_used'])
        print(f"\n⏳ Intelligent pause of {pause_time}s between agents (combined limits)...")
        time.sleep(pause_time)
        
        # ================= AGENT 2: FILTERING =================
        print("\n🔬 AGENT 2 (Gemini 2.5): Filtering with strict criteria...")
        print("-" * 50)
        
        try:
            # Request with specific rate limit control for Gemini 2.5
            response2 = self.client.safe_gemini_request(
                self.client.agent2_model,
                create_filter_prompt(candidates),
                "Agent 2",
                "gemini-2.5-flash"
            )
            result2 = response2.text.strip()
            
            # Clean JSON response
            filtered_data = clean_and_parse_json(result2, "Agent 2")
            if filtered_data is None:
                return {
                    "candidates": candidates, 
                    "error": "Agent 2 JSON parsing failed", 
                    "success": False
                }
            
            final_metaphors = filtered_data.get('metaphors', [])
            rejected_count = len(candidates) - len(final_metaphors)
            
            print(f"✅ Approved metaphors: {len(final_metaphors)}")
            print(f"❌ Rejected candidates: {rejected_count}")
            
            if final_metaphors:
                print(f"\n🎯 IDENTIFIED CONCEPTUAL METAPHORS:")
                for i, metaphor in enumerate(final_metaphors, 1):
                    print(f"\n   {i}. '{metaphor['text']}'")
                    context_preview = metaphor['context'][:100] + "..." if len(metaphor['context']) > 100 else metaphor['context']
                    print(f"      📝 Context: {context_preview}")
            
            # Complete result
            return {
                "agent1_model": "gemini-2.0-flash",
                "agent2_model": "gemini-2.5-flash", 
                "candidates": candidates,
                "final_metaphors": final_metaphors,
                "agent1_count": len(candidates),
                "agent2_count": len(final_metaphors),
                "rejected_count": rejected_count,
                "success": True
            }
            
        except Exception as e:
            print(f"❌ Error in Agent 2: {e}")
            return {
                "candidates": candidates, 
                "error": f"Agent 2 error: {str(e)}", 
                "success": False
            }
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get API usage summary"""
        return self.client.get_usage_summary()
    
    def display_detailed_results(self, result: Dict[str, Any]):
        """Display detailed analysis results"""
        if not result or not result.get('success'):
            print("❌ Analysis did not complete successfully")
            return
        
        print("\n" + "=" * 60)
        print("📊 DETAILED ANALYSIS SUMMARY")
        print("=" * 60)
        
        print(f"🔍 Agent 1 ({result['agent1_model']}): {result['agent1_count']} candidates")
        print(f"🔬 Agent 2 ({result['agent2_model']}): {result['agent2_count']} approved")
        
        if result['agent1_count'] > 0:
            print(f"📉 Filtering rate: {(result['rejected_count']/result['agent1_count']*100):.1f}% rejected")
        
        # Show combined usage
        usage = self.get_usage_summary()
        combined = usage['combined']
        by_model = usage['by_model']
        
        print(f"📊 Combined limits:")
        print(f"   System: {combined['rpd_used']}/{combined['rpd_limit']} RPD, "
              f"{combined['rpm_used']}/{combined['rpm_limit']} RPM")
        print(f"   By model: Gemini 2.0={by_model['gemini-2.0-flash']}, "
              f"Gemini 2.5={by_model['gemini-2.5-flash']}")
        
        if result['final_metaphors']:
            print(f"\n📋 FINAL CONCEPTUAL METAPHORS:")
            for i, metaphor in enumerate(result['final_metaphors'], 1):
                print(f"\n{i}. METAPHOR: '{metaphor['text']}'")
                print(f"   CONTEXT: {metaphor['context']}")
        
        print("\n✅ Analysis completed successfully")