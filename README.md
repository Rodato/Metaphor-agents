# Metaphor Analysis System

A sophisticated two-agent system for detecting conceptual metaphors in financial texts using Google Gemini models.

## Overview

This system uses two specialized AI agents to identify and validate conceptual metaphors in financial documents:

- **Agent 1 (Gemini 2.0 Flash)**: Detects metaphor candidates with high sensitivity
- **Agent 2 (Gemini 2.5 Flash)**: Validates candidates using strict linguistic criteria

The system focuses on metaphors that map physical/concrete domains (fire, weather, machines) to abstract financial concepts.

## Project Structure

```
Metaphor-agents/
├── src/
│   ├── __init__.py              # Package initialization
│   ├── metaphor_analyzer.py     # Main two-agent system
│   ├── gemini_client.py         # Gemini API client with rate limiting
│   ├── rate_limiter.py          # Combined API rate limit management
│   ├── prompt_templates.py      # Agent prompting strategies
│   ├── json_utils.py            # JSON parsing utilities
│   └── database.py              # MongoDB operations
├── config/
│   └── .env.example             # Environment variables template
├── main.py                      # Main executable script
├── requirements.txt             # Python dependencies
├── CLAUDE.md                    # Claude Code guidance
├── 6_Agents.ipynb               # Original notebook (for reference)
└── README.md                    # This file
```

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/Rodato/Metaphor-agents.git
cd Metaphor-agents
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
cp config/.env.example .env
```

Edit `.env` with your actual configuration:
```bash
# Google Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# MongoDB Configuration (for batch processing)
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/...
MONGO_DATABASE=discursos_economia
MONGO_COLLECTION=discursos
```

## Usage

### 1. Single Text Analysis

Analyze a single piece of text for metaphors:

```bash
python main.py --mode single --text "The market experienced a fire sale as investors fled to safety during the storm."
```

### 2. Batch Processing

Process multiple speeches from the database:

```bash
# Process up to 10 speeches
python main.py --mode batch --limit 10

# Process all unprocessed speeches (respects API limits)
python main.py --mode batch
```

### 3. Database Statistics

View processing statistics:

```bash
python main.py --mode stats
```

## API Configuration

### Google Gemini API

1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set it in your `.env` file as `GEMINI_API_KEY`

### Rate Limits

The system automatically manages combined API limits:
- **Combined RPM**: 10 requests per minute (most restrictive)
- **Combined RPD**: 200 requests per day (most restrictive)
- **Intelligent delays**: Between agent calls to optimize throughput

## Database Schema

For batch processing, the system expects MongoDB documents with this structure:

```javascript
{
  "_id": ObjectId,
  "Titulo": "Speech title",
  "Fecha": "Date",
  "Nombre": "Speaker name",
  "Metaphors": [
    {
      "text": "Full speech text content..."
    }
  ]
}
```

Results are stored as:

```javascript
{
  "ai_metaphors_v2": [
    {
      "text": "fire sale",
      "context": "The market experienced a fire sale..."
    }
  ],
  "ai_metaphors_v2_count": 1,
  "ai_metaphors_v2_candidates": [...],  // Initial candidates from Agent 1
  "ai_metaphors_v2_processed": true,
  "ai_metaphors_v2_stats": {
    "agent1_model": "gemini-2.0-flash",
    "agent2_model": "gemini-2.5-flash",
    "processing_time": 45.2
  }
}
```

## Metaphor Detection Criteria

### Valid Metaphors (Examples)

✅ **Accepted**: Clear domain mappings
- `"fire sales"` → FIRE (destructive) → SALES (value-destroying)
- `"weather a downturn"` → STORM → ECONOMIC CRISIS
- `"tangled picture"` → PHYSICAL ENTANGLEMENT → MARKET COMPLEXITY
- `"hub-and-spoke network"` → WHEEL STRUCTURE → MARKET ORGANIZATION

### Invalid Patterns (Examples)

❌ **Rejected**: Common expressions or technical terms
- `"take stock"` → Common idiom
- `"market participants"` → Technical terminology
- `"move forward"` → Generic expression
- `"regulatory framework"` → Standard language

## Development

### Running Tests

```bash
pytest  # If you add tests
```

### Code Formatting

```bash
black src/
flake8 src/
```

### Adding New Features

1. Create feature branch
2. Add to appropriate module in `src/`
3. Update tests and documentation
4. Submit pull request

## Troubleshooting

### Common Issues

**API Key Not Found**
```
❌ Error: GEMINI_API_KEY not found in environment variables
```
Solution: Check your `.env` file and ensure `GEMINI_API_KEY` is set.

**Rate Limit Exceeded**
```
⚠️ Daily combined limit reached (200 requests)
```
Solution: Wait for daily reset or reduce batch processing limits.

**MongoDB Connection Failed**
```
❌ Error connecting to MongoDB
```
Solution: Verify your `MONGO_URI` in the `.env` file.

**JSON Parsing Errors**
The system has multiple fallback strategies for parsing AI responses, but occasionally may fail with complex outputs. Check the console for detailed error messages.

### Performance Optimization

- **Batch Size**: Limit batch processing to respect API quotas
- **Concurrent Requests**: The system processes sequentially to avoid rate limits
- **Text Length**: Very long texts may hit token limits (handled gracefully)

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Citation

If you use this system in your research, please cite:

```bibtex
@software{metaphor_analysis_system,
  title={Two-Agent Metaphor Analysis System},
  author={Daniel Otero},
  year={2024},
  url={https://github.com/Rodato/Metaphor-agents}
}
```

## Support

- **Issues**: Report bugs and request features via GitHub Issues
- **Documentation**: See `CLAUDE.md` for detailed technical documentation
- **Original Notebook**: Reference implementation in `6_Agents.ipynb`
