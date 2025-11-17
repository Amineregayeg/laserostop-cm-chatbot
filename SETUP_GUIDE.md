# LaserOstop CM Chatbot - Setup Guide

Complete step-by-step guide to get the chatbot running.

## Quick Start (5 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Initialize database
python -m app.db

# 4. Seed test data
python scripts/dev_seed.py

# 5. Run the server
python run.py

# 6. Test in another terminal
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "Salam, nheb nhez rendez-vous"}'
```

## Detailed Setup

### Step 1: Environment Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Verify Python version
python --version  # Should be 3.11 or higher

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file
nano .env  # or your preferred editor
```

**Minimal .env configuration:**
```bash
OPENAI_API_KEY=sk-your-actual-key-here
DB_URL=sqlite:///laserostop_cm.db
VECTOR_DB_DIR=./vector_store
```

**Verify configuration:**
```python
python -c "from app.config import OPENAI_API_KEY; print('Config OK')"
```

### Step 3: Database Initialization

```bash
# Initialize database tables
python -m app.db

# Expected output:
# Database initialized successfully at: sqlite:///laserostop_cm.db
# Table counts: {'interactions': 0, 'eval_examples': 0, ...}
```

### Step 4: Data Preparation

#### Option A: Use Sample Data (Quick Start)

```bash
# Seed evaluation examples
python scripts/dev_seed.py

# Expected output:
# Added 15 sample examples
# Total evaluation examples: 15
```

#### Option B: Use Real Tunisian Dialect Dataset

```python
# Create data/processed/messages.parquet
import pandas as pd

# Your Tunisian dialect data
data = {
    "id": ["1", "2", "3"],
    "text": [
        "Ahla, nheb nhez rendez-vous",
        "Chhal thot les séances?",
        "Est-ce que le laser ça marche?"
    ],
    "source": ["manual", "manual", "manual"],
    "lang_script": ["mixed", "fr", "fr"]
}

df = pd.DataFrame(data)
df.to_parquet("data/processed/messages.parquet", index=False)
print("Dataset created successfully!")
```

```bash
# Build RAG index
python scripts/build_index.py

# Expected output:
# Loaded X valid messages
# Indexed batch 0-100...
# Index building complete
```

### Step 5: Run the Application

```bash
# Start Flask server
python run.py

# Expected output:
# * Running on http://0.0.0.0:5000
# * Debug mode: on
```

### Step 6: Test the Chatbot

**Test 1: Health Check**
```bash
curl http://localhost:5000/health
# Expected: {"status": "ok"}
```

**Test 2: Chat Request**
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Chhal thot les séances?",
    "channel": "test",
    "use_rag": true
  }'

# Expected: JSON with "reply" field
```

**Test 3: Stats Endpoint**
```bash
curl http://localhost:5000/stats

# Expected: Database and RAG statistics
```

## Running Evaluations

```bash
# Run evaluation on sample data
python scripts/run_eval.py --limit 10

# Expected output:
# EVALUATION SUMMARY
# Accuracy: XX%
# CTA Presence: XX%
# Safety Score: XX%
```

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-mock

# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_chat.py -v

# Expected: All tests should pass
```

## Verification Checklist

- [ ] Python 3.11+ installed
- [ ] Virtual environment activated
- [ ] All dependencies installed (`pip list`)
- [ ] .env file exists with valid OPENAI_API_KEY
- [ ] Database initialized (laserostop_cm.db file exists)
- [ ] Evaluation examples seeded (>0 in database)
- [ ] Flask server starts without errors
- [ ] Health endpoint returns {"status": "ok"}
- [ ] Chat endpoint returns valid responses
- [ ] Tests pass (if running pytest)

## Common Issues & Solutions

### Issue: "OPENAI_API_KEY not found"

**Cause:** Missing or invalid .env file

**Solution:**
```bash
# Verify .env exists
ls -la .env

# Check content
cat .env | grep OPENAI_API_KEY

# If missing, copy from example
cp .env.example .env
# Then edit and add your key
```

### Issue: "No module named 'app'"

**Cause:** Running from wrong directory or Python path issue

**Solution:**
```bash
# Ensure you're in project root
cd laserostop_cm
pwd  # Should end with /laserostop_cm

# Run from project root
python -m app
```

### Issue: ChromaDB collection is empty

**Cause:** RAG index not built

**Solution:**
```bash
# Verify data file exists
ls -la data/processed/messages.parquet

# Build index
python scripts/build_index.py --reset
```

### Issue: "No evaluation examples found"

**Cause:** Database not seeded

**Solution:**
```bash
# Seed with sample data
python scripts/dev_seed.py

# Verify
python -c "from app.db import get_session, EvalExample; \
  from app.db import get_session; \
  with get_session() as s: print(s.query(EvalExample).count())"
```

### Issue: Tests fail with import errors

**Cause:** Missing test dependencies

**Solution:**
```bash
# Install test dependencies
pip install pytest pytest-mock

# Run from project root
cd laserostop_cm
pytest tests/ -v
```

## Development Workflow

### 1. Adding New Features

```bash
# Create feature branch (if using git)
git checkout -b feature/my-feature

# Make changes to code

# Run tests
pytest tests/ -v

# Test manually
python run.py
# Test with curl/Postman
```

### 2. Updating System Prompt

Edit `app/chat.py`:
```python
SYSTEM_PROMPT = """
Your updated prompt...
"""
```

Test changes:
```bash
# Restart server
python run.py

# Test new behavior
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "test message"}'
```

### 3. Adding Evaluation Examples

```python
from app.db import get_session, EvalExample

with get_session() as session:
    example = EvalExample(
        input_text="New test input",
        ideal_answer="Expected response",
        category="your_category",
        sensitivity="normal"
    )
    session.add(example)

print("Example added!")
```

Run evaluation:
```bash
python scripts/run_eval.py --limit 20
```

### 4. Updating RAG Data

```bash
# Add new data to data/processed/messages.parquet

# Rebuild index
python scripts/build_index.py --reset

# Test retrieval
python -c "from app.rag import retrieve_context; \
  print(retrieve_context('test query', k=3))"
```

## Production Deployment

### Using Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn "app:create_app()" \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 120 \
  --access-logfile access.log \
  --error-logfile error.log
```

### Using Docker (Optional)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "app:create_app()", "--bind", "0.0.0.0:8000"]
```

Build and run:
```bash
docker build -t laserostop-cm .
docker run -p 8000:8000 --env-file .env laserostop-cm
```

### Environment Variables for Production

```bash
FLASK_ENV=production
FLASK_DEBUG=False
DB_URL=postgresql://user:pass@host:5432/dbname  # Use PostgreSQL
CHAT_MODEL=gpt-4o  # Use premium model
```

## Monitoring

### Database Stats

```python
from app.db import get_table_counts
print(get_table_counts())
```

### RAG Stats

```python
from app.rag import get_collection_stats
print(get_collection_stats())
```

### Recent Interactions

```python
from app.db import get_session, Interaction

with get_session() as session:
    recent = session.query(Interaction)\
        .order_by(Interaction.created_at.desc())\
        .limit(10).all()

    for interaction in recent:
        print(f"{interaction.created_at}: {interaction.user_text[:50]}...")
```

## Next Steps

1. **Collect Real Data**: Replace sample data with actual Tunisian dialect datasets
2. **Fine-tune Prompts**: Iterate on SYSTEM_PROMPT based on evaluation results
3. **Add Webhooks**: Implement WhatsApp/Meta/TikTok integrations
4. **Scale Database**: Migrate to PostgreSQL for production
5. **Add Monitoring**: Implement logging and alerting
6. **Optimize Performance**: Cache responses, optimize embeddings

## Support Resources

- **README.md**: Complete feature documentation
- **Test Files**: See tests/ for usage examples
- **Module Docstrings**: Check function docstrings for details
- **Evaluation Docs**: See app/eval.py for metric definitions

---

For questions or issues, refer to the main README.md troubleshooting section.
