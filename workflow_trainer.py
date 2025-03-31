import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkflowTrainer:
    """
    Minimal workflow trainer that:
    1. Loads existing patterns
    2. Provides pattern matching
    3. Saves new patterns
    Works with your existing flow.js and voice_processor.py
    """
    
    def __init__(self):
        self.patterns_file = Path("workflows/patterns.json")
        self.patterns = self._load_patterns()
        
    def _load_patterns(self) -> Dict:
        """Load patterns from JSON file or return defaults"""
        try:
            if self.patterns_file.exists():
                with open(self.patterns_file) as f:
                    return json.load(f)
            return self._get_default_patterns()
        except Exception as e:
            logger.error(f"Failed to load patterns: {str(e)}")
            return self._get_default_patterns()

    def _get_default_patterns(self) -> Dict:
        """Fallback patterns if file doesn't exist"""
        return {
            "targeting_patterns": [
                {
                    "keywords": ["AI", "artificial intelligence"],
                    "industries": ["SaaS", "Tech"],
                    "message_templates": [
                        "How are you currently handling {pain_point}?",
                        "Many {industry} companies use our solution for {benefit}"
                    ]
                }
            ]
        }

    def find_best_pattern(self, product_description: str) -> Optional[Dict]:
        """
        Simple keyword-based pattern matching
        Example usage:
            pattern = trainer.find_best_pattern("AI sales tool")
        """
        if not product_description or not self.patterns.get("targeting_patterns"):
            return None
            
        product_lower = product_description.lower()
        
        for pattern in self.patterns["targeting_patterns"]:
            keywords = pattern.get("keywords", [])
            if any(kw.lower() in product_lower for kw in keywords):
                return pattern
        return None

    def save_patterns(self, patterns: Dict):
        """Save patterns to JSON file"""
        try:
            self.patterns_file.parent.mkdir(exist_ok=True)
            with open(self.patterns_file, 'w') as f:
                json.dump(patterns, f, indent=2)
            logger.info(f"Saved patterns to {self.patterns_file}")
        except Exception as e:
            logger.error(f"Failed to save patterns: {str(e)}")

    def get_suggested_message(self, product_desc: str) -> str:
        """
        Get a suggested message template for a product
        Basic version that works with your existing flow.js
        """
        pattern = self.find_best_pattern(product_desc)
        if pattern and pattern.get("message_templates"):
            return pattern["message_templates"][0]  # Return first template
        return "Tell me more about your product and target customers"

# Example usage that works with your current setup:
if __name__ == "__main__":
    trainer = WorkflowTrainer()
    
    # This matches your existing flow.js data structure
    test_product = "AI-powered sales assistant"
    
    pattern = trainer.find_best_pattern(test_product)
    print(f"Matched pattern: {pattern}")
    
    message = trainer.get_suggested_message(test_product)
    print(f"Suggested message: {message}")