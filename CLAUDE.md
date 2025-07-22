# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a research project for analyzing conceptual metaphors in financial texts using a dual-agent system. The system uses two Google Gemini models:

- **Agent 1 (Gemini 2.0 Flash)**: Detects metaphor candidates with high sensitivity
- **Agent 2 (Gemini 2.5 Flash)**: Validates and filters candidates using strict linguistic criteria

The project analyzes financial documents (Fed speeches) stored in MongoDB and identifies conceptual metaphors that map physical/concrete domains to abstract financial concepts.

## Architecture

### Core Components

1. **6_Agents.ipynb** - Main Jupyter notebook containing the complete dual-agent system
   - Agent prompting strategies for metaphor detection and validation
   - Rate limiting system for API management
   - MongoDB integration for document processing
   - Automated batch processing capabilities

2. **Key Classes and Functions**:
   - `RateLimiter`: Manages combined API rate limits across both Gemini models
   - `analyze_with_two_agents()`: Main processing pipeline
   - `create_candidate_prompt()`: Agent 1 prompt for initial detection
   - `create_filter_prompt()`: Agent 2 prompt for validation
   - `safe_gemini_request()`: Rate-limited API wrapper

### Data Flow

1. Load financial text from MongoDB collection `discursos_economia.discursos`
2. Agent 1 identifies metaphor candidates using detection prompts
3. System applies intelligent delays based on combined rate limits
4. Agent 2 validates candidates against strict linguistic criteria
5. Results stored back to MongoDB with detailed metadata

## Development Setup

### Prerequisites

```bash
pip install google-generativeai pymongo
```

### API Configuration

Requires Google Gemini API key stored in environment or Google Colab userdata as `GEMINI_API_KEY_2`.

### MongoDB Configuration

Uses MongoDB Atlas cluster:
- Database: `discursos_economia` 
- Collection: `discursos`
- Connection string stored in notebook

## Key Development Patterns

### Rate Limiting Strategy

The system uses combined rate limits to respect API quotas:
- 10 RPM (requests per minute) combined
- 200 RPD (requests per day) combined  
- Intelligent delays between agent calls
- Per-model tracking for monitoring

### Error Handling

- JSON parsing with multiple fallback strategies
- Graceful handling of API failures
- Comprehensive logging for debugging

### Prompt Engineering

- Domain-specific examples for metaphor identification
- Strict filtering criteria to reduce false positives
- JSON response format enforcement

## Metaphor Analysis Criteria

### Valid Metaphors (examples)

- "fire sales" → FIRE domain mapped to destructive financial sales
- "tangled picture" → PHYSICAL ENTANGLEMENT mapped to market complexity
- "hub-and-spoke network" → WHEEL STRUCTURE mapped to market organization

### Invalid Patterns (rejected)

- Standard financial terminology
- Common idioms without systematic domain mapping
- Technical jargon without metaphorical structure

## Usage Notes

- The notebook is designed for Google Colab environment
- Processes documents in batches respecting API limits
- Stores comprehensive metadata for each analysis
- Supports resuming interrupted processing sessions
- Includes detailed progress tracking and statistics

## MongoDB Schema

Documents are enhanced with AI analysis results:

```javascript
{
  "ai_metaphors_v2": [...],           // Final validated metaphors
  "ai_metaphors_v2_count": Number,    // Count of metaphors found
  "ai_metaphors_v2_candidates": [...], // Initial candidates from Agent 1
  "ai_metaphors_v2_method": String,    // Processing method identifier
  "ai_metaphors_v2_stats": {          // Detailed processing statistics
    "agent1_model": String,
    "agent2_model": String,
    "processing_time": Number
  }
}
```