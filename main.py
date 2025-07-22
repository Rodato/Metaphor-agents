#!/usr/bin/env python3
"""
Main script for metaphor analysis system

Usage:
    python main.py --mode single --text "Your text here"
    python main.py --mode batch --limit 10
    python main.py --mode stats
"""

import argparse
import json
import os
import sys
import time
import traceback
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.metaphor_analyzer import MetaphorAnalyzer
from src.database import MetaphorDatabase


def load_config():
    """Load configuration from environment variables"""
    # Load .env file if exists
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    
    config = {
        'gemini_api_key': os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'),
        'mongo_uri': os.getenv('MONGO_URI'),
        'mongo_database': os.getenv('MONGO_DATABASE', 'discursos_economia'),
        'mongo_collection': os.getenv('MONGO_COLLECTION', 'discursos'),
        'max_speeches_per_run': int(os.getenv('MAX_SPEECHES_PER_RUN', '50')),
        'processing_delay': int(os.getenv('PROCESSING_DELAY', '60'))
    }
    
    return config


def analyze_single_text(text: str, config: dict):
    """Analyze a single text for metaphors"""
    print("🔍 SINGLE TEXT ANALYSIS")
    print("=" * 50)
    
    if not config['gemini_api_key']:
        print("❌ Error: GEMINI_API_KEY not found in environment variables")
        return
    
    try:
        # Initialize analyzer
        analyzer = MetaphorAnalyzer(config['gemini_api_key'])
        
        # Analyze text
        result = analyzer.analyze_text(text)
        
        if result and result.get('success'):
            # Display detailed results
            analyzer.display_detailed_results(result)
            
            # Show JSON result
            print(f"\n📄 COMPLETE RESULT (JSON):")
            print("-" * 40)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("\n❌ Analysis failed. Check errors above.")
            if result:
                print(f"Error: {result.get('error', 'Unknown')}")
    
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        print(f"   Traceback: {traceback.format_exc()}")


def batch_process_speeches(config: dict, limit: int = None):
    """Batch process speeches from database"""
    print("🚀 BATCH PROCESSING MODE")
    print("=" * 50)
    
    # Check required config
    if not config['gemini_api_key']:
        print("❌ Error: GEMINI_API_KEY not found in environment variables")
        return
    
    if not config['mongo_uri']:
        print("❌ Error: MONGO_URI not found in environment variables")
        return
    
    try:
        # Initialize components
        analyzer = MetaphorAnalyzer(config['gemini_api_key'])
        db = MetaphorDatabase(
            config['mongo_uri'], 
            config['mongo_database'], 
            config['mongo_collection']
        )
        
        # Connect to database
        db.connect()
        
        # Get statistics
        stats = db.get_statistics()
        print(f"📊 DATABASE STATISTICS:")
        print(f"   Total speeches: {stats['total_speeches']}")
        print(f"   Already processed: {stats['processed_speeches']}")
        print(f"   Pending: {stats['unprocessed_speeches']}")
        print(f"   Progress: {stats['processing_percentage']:.1f}%")
        
        if stats['unprocessed_speeches'] == 0:
            print("🎉 All speeches are already processed!")
            db.close()
            return
        
        # Check API limits
        usage_summary = analyzer.get_usage_summary()
        requests_used = usage_summary['combined']['rpd_used']
        requests_available = 200 - requests_used  # Combined daily limit
        speeches_possible = requests_available // 2  # 2 requests per speech
        
        print(f"\n🔋 API STATUS:")
        print(f"   Requests used today: {requests_used}/200")
        print(f"   Requests available: {requests_available}")
        print(f"   Speeches you can process: {speeches_possible}")
        
        if speeches_possible == 0:
            print("❌ Not enough requests available to process speeches")
            db.close()
            return
        
        # Determine processing limit
        process_limit = limit or min(speeches_possible, config['max_speeches_per_run'])
        
        # Get speeches to process
        unprocessed_speeches = db.get_unprocessed_speeches(process_limit)
        print(f"🎯 Processing {len(unprocessed_speeches)} speeches...")
        
        # Process each speech
        success_count = 0
        error_count = 0
        start_time = time.time()
        
        for i, speech in enumerate(unprocessed_speeches, 1):
            print(f"\n{'='*60}")
            print(f"🔢 SPEECH {i}/{len(unprocessed_speeches)}")
            
            speech_id = speech['_id']
            titulo = speech.get('Titulo', 'No title')
            if len(titulo) > 80:
                titulo = titulo[:80] + "..."
            fecha = speech.get('Fecha', 'No date')
            nombre = speech.get('Nombre', 'No name')
            
            print(f"📝 {titulo}")
            print(f"📅 {fecha} - {nombre}")
            
            try:
                # Extract text
                speech_text = db.extract_text_from_speech(speech)
                if not speech_text or len(speech_text.strip()) < 100:
                    print(f"⚠️ Text too short: {len(speech_text) if speech_text else 0} characters")
                    error_count += 1
                    continue
                
                print(f"📄 Text length: {len(speech_text):,} characters")
                
                # Process with two-agent system
                processing_start = time.time()
                result = analyzer.analyze_text(speech_text)
                processing_time = time.time() - processing_start
                
                if result and result.get('success'):
                    # Save to database
                    saved = db.save_analysis_result(speech_id, result, processing_time)
                    
                    if saved:
                        success_count += 1
                        metaphors_found = result.get('final_metaphors', [])
                        print(f"✅ SUCCESS: {len(metaphors_found)} metaphors found")
                        
                        if metaphors_found:
                            for j, metaphor in enumerate(metaphors_found[:3], 1):
                                print(f"   {j}. '{metaphor['text']}'")
                            if len(metaphors_found) > 3:
                                print(f"   ... and {len(metaphors_found) - 3} more")
                    else:
                        print("❌ Error saving to database")
                        error_count += 1
                else:
                    print("❌ Error in metaphor analysis")
                    if result:
                        print(f"   Error: {result.get('error', 'Unknown')}")
                    error_count += 1
                    
            except Exception as e:
                print(f"❌ EXCEPTION: {str(e)}")
                error_count += 1
            
            # Show progress every 5 speeches
            if i % 5 == 0 or i == len(unprocessed_speeches):
                elapsed = time.time() - start_time
                remaining = len(unprocessed_speeches) - i
                avg_time = elapsed / i if i > 0 else 0
                eta = remaining * avg_time
                
                print(f"\n📊 PROGRESS:")
                print(f"   Completed: {i}/{len(unprocessed_speeches)} ({i/len(unprocessed_speeches)*100:.1f}%)")
                print(f"   Successful: {success_count} | Errors: {error_count}")
                print(f"   Time elapsed: {elapsed/60:.1f} min")
                if remaining > 0:
                    print(f"   Estimated time remaining: {eta/60:.1f} min")
        
        # Final statistics
        total_time = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"🎯 PROCESSING COMPLETED")
        print(f"{'='*60}")
        print(f"✅ Successfully processed speeches: {success_count}")
        print(f"❌ Errors: {error_count}")
        print(f"⏱️ Total time: {total_time/60:.1f} minutes")
        if success_count + error_count > 0:
            print(f"📊 Average per speech: {total_time/(success_count + error_count):.1f} seconds")
        
        # Updated statistics
        final_stats = db.get_statistics()
        print(f"\n📈 FINAL STATISTICS:")
        print(f"   Total processed: {final_stats['processed_speeches']}/{final_stats['total_speeches']} ({final_stats['processing_percentage']:.1f}%)")
        print(f"   Remaining: {final_stats['unprocessed_speeches']}")
        
        # Final API usage
        final_usage = analyzer.get_usage_summary()
        print(f"\n🔋 FINAL API USAGE:")
        print(f"   Requests used today: {final_usage['combined']['rpd_used']}/200")
        print(f"   Requests remaining: {200 - final_usage['combined']['rpd_used']}")
        
        # Close connection
        db.close()
        print("\n🎉 Batch processing completed!")
        
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        print(f"   Traceback: {traceback.format_exc()}")


def show_statistics(config: dict):
    """Show database statistics"""
    print("📊 DATABASE STATISTICS")
    print("=" * 50)
    
    if not config['mongo_uri']:
        print("❌ Error: MONGO_URI not found in environment variables")
        return
    
    try:
        # Connect to database
        db = MetaphorDatabase(
            config['mongo_uri'], 
            config['mongo_database'], 
            config['mongo_collection']
        )
        db.connect()
        
        # Get and show statistics
        stats = db.get_statistics()
        print(f"📈 Processing Statistics:")
        print(f"   Total speeches: {stats['total_speeches']}")
        print(f"   Processed: {stats['processed_speeches']}")
        print(f"   Pending: {stats['unprocessed_speeches']}")
        print(f"   Progress: {stats['processing_percentage']:.1f}%")
        
        # Show sample of processed speeches
        if stats['processed_speeches'] > 0:
            print(f"\n📋 Sample of processed speeches:")
            samples = db.get_processed_speeches_sample(5)
            for i, sample in enumerate(samples, 1):
                titulo = sample.get('Titulo', 'No title')
                if len(titulo) > 60:
                    titulo = titulo[:60] + "..."
                metaphor_count = sample.get('ai_metaphors_v2_count', 0)
                print(f"   {i}. {titulo} - {metaphor_count} metaphors")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Metaphor Analysis System')
    parser.add_argument('--mode', choices=['single', 'batch', 'stats'], required=True,
                       help='Processing mode')
    parser.add_argument('--text', type=str, help='Text to analyze (for single mode)')
    parser.add_argument('--limit', type=int, help='Max speeches to process (for batch mode)')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    print("🚀 METAPHOR ANALYSIS SYSTEM")
    print("=" * 50)
    
    if args.mode == 'single':
        if not args.text:
            print("❌ Error: --text is required for single mode")
            return
        analyze_single_text(args.text, config)
    
    elif args.mode == 'batch':
        batch_process_speeches(config, args.limit)
    
    elif args.mode == 'stats':
        show_statistics(config)


if __name__ == "__main__":
    main()