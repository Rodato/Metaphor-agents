"""
MongoDB database operations for metaphor analysis
"""
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any
from pymongo import MongoClient


class MetaphorDatabase:
    """MongoDB operations for metaphor analysis project"""
    
    def __init__(self, mongo_uri: str, database_name: str = "discursos_economia", 
                 collection_name: str = "discursos"):
        """
        Initialize database connection
        
        Args:
            mongo_uri: MongoDB connection string
            database_name: Database name
            collection_name: Collection name
        """
        self.mongo_uri = mongo_uri
        self.database_name = database_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            print(f"🔗 Connected to MongoDB: {self.database_name}.{self.collection_name}")
        except Exception as e:
            print(f"❌ Error connecting to MongoDB: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            print("🔐 MongoDB connection closed")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        if not self.collection:
            raise RuntimeError("Database not connected")
        
        total_speeches = self.collection.count_documents({})
        processed_speeches = self.collection.count_documents({"ai_metaphors_v2_processed": True})
        unprocessed_speeches = total_speeches - processed_speeches
        
        return {
            "total_speeches": total_speeches,
            "processed_speeches": processed_speeches,
            "unprocessed_speeches": unprocessed_speeches,
            "processing_percentage": (processed_speeches / total_speeches * 100) if total_speeches > 0 else 0
        }
    
    def get_unprocessed_speeches(self, limit: Optional[int] = None) -> List[Dict]:
        """Get speeches that haven't been processed yet"""
        if not self.collection:
            raise RuntimeError("Database not connected")
        
        query = {
            "$or": [
                {"ai_metaphors_v2": {"$exists": False}},
                {"ai_metaphors_v2_processed": {"$ne": True}}
            ]
        }
        
        cursor = self.collection.find(query)
        if limit:
            cursor = cursor.limit(limit)
        
        return list(cursor)
    
    def extract_text_from_speech(self, speech: Dict) -> Optional[str]:
        """Extract text from speech document"""
        metaphors_array = speech.get('Metaphors', [])
        
        if not metaphors_array or len(metaphors_array) == 0:
            print("⚠️ No text in Metaphors field")
            return None
        
        # Text is in the first element of the array
        first_item = metaphors_array[0]
        if isinstance(first_item, dict) and 'text' in first_item:
            return first_item['text']
        elif isinstance(first_item, str):
            return first_item
        else:
            print("⚠️ Unrecognized text format")
            return None
    
    def save_analysis_result(self, speech_id, analysis_result: Dict[str, Any], 
                           processing_time: float) -> bool:
        """Save metaphor analysis result to database"""
        if not self.collection:
            raise RuntimeError("Database not connected")
        
        try:
            metaphors_found = analysis_result.get('final_metaphors', [])
            candidates_found = analysis_result.get('candidates', [])
            
            update_data = {
                "ai_metaphors_v2": metaphors_found,
                "ai_metaphors_v2_count": len(metaphors_found),
                "ai_metaphors_v2_candidates": candidates_found,
                "ai_metaphors_v2_method": "two_agent_gemini_2.0_2.5",
                "ai_metaphors_v2_processed": True,
                "ai_metaphors_v2_processed_at": datetime.now(),
                "ai_metaphors_v2_stats": {
                    "agent1_model": analysis_result.get('agent1_model'),
                    "agent2_model": analysis_result.get('agent2_model'),
                    "agent1_count": analysis_result.get('agent1_count', 0),
                    "agent2_count": analysis_result.get('agent2_count', 0),
                    "rejected_count": analysis_result.get('rejected_count', 0),
                    "processing_time": processing_time
                }
            }
            
            # Save to MongoDB
            save_result = self.collection.update_one(
                {"_id": speech_id},
                {"$set": update_data}
            )
            
            return save_result.modified_count > 0
            
        except Exception as e:
            print(f"❌ Error saving to database: {e}")
            print(f"   Traceback: {traceback.format_exc()}")
            return False
    
    def get_processed_speeches_sample(self, limit: int = 5) -> List[Dict]:
        """Get sample of processed speeches for verification"""
        if not self.collection:
            raise RuntimeError("Database not connected")
        
        return list(self.collection.find(
            {"ai_metaphors_v2_processed": True},
            {
                "Titulo": 1,
                "Fecha": 1, 
                "Nombre": 1,
                "ai_metaphors_v2_count": 1,
                "ai_metaphors_v2": 1
            }
        ).limit(limit))