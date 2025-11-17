# LaserOstop CM Chatbot

A production-ready community manager chatbot for **LaserOstop Tunisia**, featuring RAG (Retrieval-Augmented Generation), GPT-5-nano integration, comprehensive evaluation framework, and a full-featured testing interface with detailed logging.

## Overview

This chatbot serves as an intelligent community manager for LaserOstop Tunisia's laser stop-smoking service. It communicates in Tunisian dialect (Derja), mixing Arabic and French naturally, and provides accurate information about laser therapy for smoking cessation.

### Key Features

#### Backend
- **RAG-Enhanced Responses**: Uses Tunisian dialect social media datasets for context-aware responses
- **GPT-5-nano Integration**: Powered by OpenAI's latest GPT-5-nano model (`gpt-5-nano-2025-08-07`)
- **Multilingual Support**: Handles Arabic, French, and Tunisian dialect seamlessly
- **Voice Message Support**: Whisper API integration for audio transcription
- **Comprehensive Evaluation**: Built-in evaluation framework with quality metrics
- **Multi-Channel Ready**: Prepared for WhatsApp, Meta (FB/IG), and TikTok integration
- **Database Logging**: Full conversation tracking and analytics

#### Frontend Testing Interface
- **Comprehensive Logging**: Real-time logs from Frontend, Backend, AI/GPT, and Errors
- **Performance Monitoring**: Track response times, token usage, and success rates
- **Log Filtering**: Toggle visibility of different log sources
- **Export Functionality**: Export all logs and messages to JSON for analysis
- **RAG Toggle**: Enable/disable RAG for A/B testing
- **Modern UI**: Clean, responsive interface supporting Arabic and Latin scripts

## Architecture

```
┌─────────────────┐
│  User Message   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│   Flask API     │◄────►│  Webhooks    │
└────────┬────────┘      │  (WhatsApp,  │
         │               │   Meta, etc) │
         ▼               └──────────────┘
┌─────────────────┐
│   Chat Logic    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────────┐
│  RAG   │ │  GPT-4o    │
│ChromaDB│ │  OpenAI    │
└────────┘ └────────────┘
    │
    ▼
┌─────────────────┐
│   SQLite DB     │
│  (Interactions, │
│   Evaluations)  │
└─────────────────┘
```

## Prerequisites

- Python 3.11+
- OpenAI API key
- 2GB+ RAM (for embedding model)
- ~1GB disk space (for vector database)

## Installation

### 1. Clone and Setup Environment

```bash
cd laserostop_cm

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env  # or use your preferred editor
```

Required configuration in `.env`:
```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 3. Initialize Database

```bash
# Initialize database tables
python -m app.db
```

### 4. Seed Evaluation Examples (Development)

```bash
# Seed database with sample evaluation examples
python scripts/dev_seed.py
```

## Preparing Data

### RAG Dataset Format

The RAG system expects a Parquet file with Tunisian dialect messages at:
`data/processed/messages.parquet`

**Required Schema:**
- `id` (string/int): Unique identifier
- `text` (string): Message text in Tunisian dialect
- `source` (string): Data source (e.g., "TUNIZI", "TSAC", "manual")
- `lang_script` (string): Language/script indicator ("ar", "fr", "mixed")

**Example Python code to create the file:**
```python
import pandas as pd

data = {
    "id": ["msg_001", "msg_002", "msg_003"],
    "text": [
        "Ahla, nheb nhez rendez-vous pour laser anti-tabac",
        "Chhal thot les séances متاع laser?",
        "Le laser ça marche vraiment pour arrêter de fumer?"
    ],
    "source": ["manual", "manual", "manual"],
    "lang_script": ["mixed", "mixed", "fr"]
}

df = pd.DataFrame(data)
df.to_parquet("data/processed/messages.parquet", index=False)
```

### Build RAG Index

```bash
# Build vector index from prepared data
python scripts/build_index.py

# Or rebuild from scratch
python scripts/build_index.py --reset
```

## Running the Application

### Backend Server

Start the Flask backend server:

```bash
# Using the run script
python run.py

# The server will start at http://localhost:5000
```

### Frontend Testing Interface

After starting the backend, open the testing interface:

```bash
# Option 1: Python HTTP Server
cd frontend
python -m http.server 8080

# Then open in browser: http://localhost:8080
```

**Or** simply open `frontend/index.html` directly in your browser.

See [frontend/README.md](frontend/README.md) for detailed testing interface documentation.

### Production Deployment

For production, use a WSGI server like Gunicorn:

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn "app:create_app()" --bind 0.0.0.0:8000 --workers 4
```

## API Endpoints

### Health Check
```bash
GET /health

Response:
{
  "status": "ok"
}
```

### Chat Endpoint
```bash
POST /chat
Content-Type: application/json

Request:
{
  "text": "Chhal thot les séances?",
  "user_id": "optional-user-id",
  "channel": "whatsapp",
  "use_rag": true,
  "use_history": false
}

Response:
{
  "reply": "Les séances عندنا prix raisonnable...",
  "model_version": "gpt-4o-mini",
  "rag_used": true,
  "rag_version": "rag_v1"
}
```

### Statistics Endpoint
```bash
GET /stats

Response:
{
  "database": {
    "interactions": 1234,
    "eval_examples": 50,
    "eval_runs": 10,
    "eval_results": 500
  },
  "rag": {
    "name": "laserostop_tunisian_messages",
    "count": 5000
  }
}
```

## Testing the Chatbot

### Quick Test via cURL

```bash
# Basic chat test
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Nheb nhez rendez-vous",
    "channel": "test",
    "use_rag": true
  }'
```

### Interactive Testing

```python
# In Python interactive shell
from app.chat import chat_with_user

# Test a message
reply = chat_with_user(
    user_text="Chhal thot les séances?",
    channel="test",
    use_rag=True
)
print(reply)
```

## Evaluation

### Running Evaluations

```bash
# Run evaluation on all examples
python scripts/run_eval.py --limit 50

# Evaluate specific model
python scripts/run_eval.py --model gpt-4o --limit 100

# Evaluate without RAG
python scripts/run_eval.py --no-rag --limit 30

# Filter by category
python scripts/run_eval.py --category booking --limit 20

# Save results to file
python scripts/run_eval.py --limit 100 --output results.json
```

### Evaluation Metrics

The evaluation framework computes:

1. **Accuracy Score**: Percentage of acceptable answers (fuzzy matching + keyword coverage)
2. **CTA Presence Rate**: Percentage of responses with call-to-action
3. **Safety Score**: Percentage of responses without medical advice risks
4. **Error Breakdown**: Classification of error types

### Viewing Results

```python
from app.eval import get_eval_run_summary

# Get summary of a specific run
summary = get_eval_run_summary(eval_run_id=1)
print(summary)

# Compare two evaluation runs
from app.eval import compare_eval_runs
comparison = compare_eval_runs(run_id_1=1, run_id_2=2)
print(comparison)
```

## Testing

### Frontend Testing Interface

The comprehensive testing interface provides:
- Real-time chat interface with Tunisian dialect support
- Complete logging system showing Frontend, Backend, AI, and Error logs
- Performance metrics (response time, token usage, success rate)
- Log filtering and export capabilities
- RAG toggle for A/B testing

**Quick Start:**
1. Start backend: `python run.py`
2. Open frontend: `cd frontend && python -m http.server 8080`
3. Navigate to: `http://localhost:8080`

See [frontend/README.md](frontend/README.md) for complete testing guide.

### Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_chat.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## Webhook Integration (Future)

The application includes webhook stubs for future integration:

### WhatsApp Business API

**Endpoint**: `POST /webhook/whatsapp`

**TODO:**
1. Configure webhook verification token
2. Parse incoming message payloads
3. Download media (audio messages)
4. Send replies via WhatsApp API

**Resources**: [WhatsApp Business API Documentation](https://developers.facebook.com/docs/whatsapp)

### Meta (Facebook/Instagram)

**Endpoint**: `POST /webhook/meta`

**TODO:**
1. Set up Meta app and page access tokens
2. Parse Messenger/Instagram message events
3. Handle different message types
4. Send replies via Send API

**Resources**: [Messenger Platform Documentation](https://developers.facebook.com/docs/messenger-platform)

### TikTok

**Endpoint**: `POST /webhook/tiktok`

**TODO:**
1. Register TikTok Business application
2. Implement webhook authentication
3. Parse comment/message events
4. Send replies via TikTok API

**Resources**: [TikTok for Business API](https://developers.tiktok.com/)

## Project Structure

```
laserostop_cm/
├── app/                     # Backend application
│   ├── __init__.py          # Flask app factory
│   ├── api.py               # API routes
│   ├── chat.py              # Chat logic (RAG + GPT-5)
│   ├── rag.py               # Vector DB and retrieval
│   ├── asr.py               # Whisper audio transcription
│   ├── db.py                # Database models
│   ├── eval.py              # Evaluation framework
│   └── config.py            # Configuration
├── frontend/                # Testing interface
│   ├── index.html           # Main UI
│   ├── styles.css           # Styling
│   ├── app.js               # Frontend logic
│   └── README.md            # Frontend documentation
├── data/
│   ├── raw/                 # Raw datasets
│   ├── processed/           # Processed datasets
│   └── eval_sets/           # Evaluation sets
├── scripts/
│   ├── build_index.py       # Build RAG index
│   ├── run_eval.py          # Run evaluations
│   └── dev_seed.py          # Seed dev data
├── tests/
│   ├── test_chat.py
│   ├── test_rag.py
│   └── test_eval.py
├── requirements.txt
├── .env.example
├── run.py                   # Application entry point
└── README.md
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `DB_URL` | Database URL | `sqlite:///laserostop_cm.db` |
| `VECTOR_DB_DIR` | Vector store directory | `./vector_store` |
| `EMBEDDING_MODEL` | Embedding model name | `intfloat/multilingual-e5-base` |
| `CHAT_MODEL` | OpenAI chat model | `gpt-5-nano-2025-08-07` |
| `ASR_MODEL` | Whisper model | `whisper-1` |
| `FLASK_ENV` | Flask environment | `development` |

### Model Selection

**GPT-5-nano** (default - `gpt-5-nano-2025-08-07`):
- Latest OpenAI model with advanced reasoning
- Optimized for complex conversations
- Native Tunisian dialect understanding
- Uses `max_completion_tokens` instead of `max_tokens`
- Does not support `temperature` parameter

**Alternative Models**:
To switch models, set in `.env`:
```bash
# Use GPT-4o
CHAT_MODEL=gpt-4o

# Use GPT-4o-mini (lower cost)
CHAT_MODEL=gpt-4o-mini
```

**Note**: The code automatically detects GPT-5 models and adjusts parameters accordingly.

## Database Schema

### Interactions Table
Stores all user conversations:
- User and assistant messages
- Channel information
- Model and RAG versions
- Flags (CTA, medical risk, etc.)
- Timestamps

### EvalExample Table
Gold standard evaluation examples:
- Input text
- Ideal answer
- Category (booking, price, medical, etc.)
- Sensitivity level

### EvalRun Table
Batch evaluation metadata:
- Model and RAG versions
- Aggregate metrics (accuracy, safety, CTA rate)
- Number of examples
- Notes

### EvalResult Table
Individual evaluation results:
- Link to eval run and example
- Predicted answer
- Acceptance status
- Error classification

## Performance Optimization

### RAG Optimization
- **Batch Size**: Adjust `--batch-size` in `build_index.py` (default: 100)
- **Retrieval K**: Modify `DEFAULT_RETRIEVAL_K` in `config.py` (default: 5)
- **Embedding Model**: Consider smaller models for faster encoding

### API Optimization
- **Caching**: Implement response caching for common queries
- **Rate Limiting**: Use Flask-Limiter for API rate limiting
- **Workers**: Scale Gunicorn workers based on CPU cores

### Database Optimization
- **PostgreSQL**: For production, migrate from SQLite to PostgreSQL (Neon, etc.)
- **Indexes**: Database models include indexes on frequently queried fields
- **Archiving**: Regularly archive old interactions to improve query speed

## Troubleshooting

### Common Issues

**Issue**: `OPENAI_API_KEY not found`
```bash
# Solution: Ensure .env file exists and contains valid API key
cp .env.example .env
# Edit .env and add your API key
```

**Issue**: `ChromaDB collection is empty`
```bash
# Solution: Build RAG index from prepared data
python scripts/build_index.py --reset
```

**Issue**: `No evaluation examples found`
```bash
# Solution: Seed database with examples
python scripts/dev_seed.py
```

**Issue**: `Import errors in tests`
```bash
# Solution: Install dev dependencies and run from project root
pip install pytest pytest-mock
cd laserostop_cm
pytest tests/ -v
```

## Development Workflow

### Adding New Evaluation Examples

```python
from app.db import get_session, EvalExample

with get_session() as session:
    example = EvalExample(
        input_text="Your test input in Tunisian dialect",
        ideal_answer="Expected response",
        category="booking",
        sensitivity="normal"
    )
    session.add(example)
```

### Updating System Prompt

Edit `SYSTEM_PROMPT` in `app/chat.py`:
```python
SYSTEM_PROMPT = """
Your updated prompt here...
"""
```

### Adding Custom Evaluation Metrics

Extend `app/eval.py` with new metric functions:
```python
def my_custom_metric(predicted: str, ideal: str) -> float:
    # Your metric logic
    return score
```

## Monitoring and Analytics

### View Interaction Stats

```python
from app.db import get_table_counts

counts = get_table_counts()
print(f"Total interactions: {counts['interactions']}")
```

### Analyze Error Patterns

```python
from app.db import get_session, EvalResult

with get_session() as session:
    errors = session.query(
        EvalResult.error_type,
        func.count(EvalResult.id)
    ).group_by(EvalResult.error_type).all()

    for error_type, count in errors:
        print(f"{error_type}: {count}")
```

## Contributing

When contributing to this project:

1. Follow existing code style and structure
2. Add docstrings to all functions
3. Write tests for new features
4. Update README with new functionality
5. Use type hints where applicable

## Security Considerations

- **API Keys**: Never commit `.env` file to version control
- **Input Validation**: All user inputs are validated before processing
- **Medical Advice**: System prompt includes strict medical disclaimers
- **Rate Limiting**: Implement rate limiting for production deployments
- **HTTPS**: Always use HTTPS in production

## License

This project is proprietary software developed for LaserOstop Tunisia.

## Support

For issues or questions:
- Check troubleshooting section above
- Review test files for usage examples
- Check module docstrings for detailed function documentation

---

**Built with**: Python, Flask, OpenAI GPT-4o, ChromaDB, SQLAlchemy, Sentence Transformers
