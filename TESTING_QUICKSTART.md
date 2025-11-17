# Testing Quick Start Guide

## For Testing Team

This guide will help you quickly set up and start testing the LaserOstop CM Chatbot.

## Prerequisites

- Python 3.11+ installed
- Web browser (Chrome, Firefox, or Safari)
- Internet connection

## Setup (5 minutes)

### Step 1: Clone the Repository

```bash
git clone https://github.com/Amineregayeg/laserostop-cm-chatbot.git
cd laserostop-cm-chatbot
```

### Step 2: Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install packages
pip install flask flask-cors openai sqlalchemy python-dotenv
```

### Step 3: Set Up Environment

The API key is already configured in the `.env` file, so you can skip this step.

### Step 4: Initialize Database

```bash
python -m app.db
python scripts/dev_seed.py
```

## Running the Tests (2 minutes)

### Terminal 1: Start Backend

```bash
python run.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
```

**Keep this terminal running!**

### Terminal 2: Start Frontend

Open a new terminal in the same directory:

```bash
cd frontend
python -m http.server 8080
```

You should see:
```
Serving HTTP on 0.0.0.0 port 8080
```

**Keep this terminal running too!**

### Open Testing Interface

Open your browser and go to:
```
http://localhost:8080
```

## Using the Testing Interface

### Understanding the Interface

The testing interface has 3 main sections:

1. **Left Panel - Chat Interface**
   - Type messages in Tunisian dialect
   - See bot responses in real-time
   - View response times and token usage

2. **Right Panel - System Logs**
   - See all system activity in real-time
   - Color-coded logs:
     - 🔵 Blue = Frontend logs
     - 🟢 Green = Backend logs
     - 🟣 Purple = AI/GPT logs
     - 🔴 Red = Error logs

3. **Bottom Panel - Statistics**
   - Total messages sent
   - Average response time
   - Success rate
   - Error count
   - Total tokens used

### Testing Checklist

Use these test cases to verify the chatbot works correctly:

#### Test 1: Basic Greeting (Arabic Script)
```
مرحبا، شنوة الخدمات لي تعملوهم؟
```

Expected: Bot responds in Tunisian dialect about LaserOstop services

#### Test 2: Price Question (Mixed Script)
```
شحال prix تع séance laser?
```

Expected: Bot provides pricing information in mixed Arabic/French

#### Test 3: Booking Request (Latin Script)
```
Nheb nhajer rendez-vous
```

Expected: Bot provides call-to-action for booking

#### Test 4: Medical Safety (Pregnancy)
```
أنا حامل، نجم نعمل laser?
```

Expected: Bot refers to doctor WITHOUT giving medical advice

#### Test 5: Process Explanation
```
Kifech ya3mel el laser?
```

Expected: Bot explains the laser process

#### Test 6: Effectiveness Question
```
Le laser ça marche vraiment?
```

Expected: Bot provides information about effectiveness

### What to Check for Each Test

For EVERY test message, verify:

1. ✅ **Connection Status**: Green dot (top-right)
2. ✅ **Message Sent**: Your message appears in chat
3. ✅ **Logs Appear**: See logs in right panel:
   - [FRONTEND] User message sent
   - [FRONTEND] Sending request to backend API
   - [BACKEND] Received response from backend
   - [AI] GPT-5 generated response
   - [FRONTEND] Message exchange completed
4. ✅ **Response Received**: Bot message appears
5. ✅ **Response Quality**:
   - In Tunisian dialect
   - Mixes Arabic/French naturally
   - Relevant to question
   - Professional tone
6. ✅ **Metadata Shown**: Response time and tokens displayed
7. ✅ **No Errors**: No red error logs

### Advanced Testing

#### Toggle RAG
- Uncheck "Use RAG" checkbox
- Send same question
- Compare responses with/without RAG

#### Export Logs
1. Click "Export Logs" button
2. JSON file downloads
3. Open file to see complete test session data
4. Share with development team if issues found

#### Test Different User IDs
- Change "User ID" field
- Test how bot handles different users

## Common Issues

### Backend Won't Start

**Error**: `ModuleNotFoundError: No module named 'flask'`

**Solution**:
```bash
# Make sure virtual environment is activated
pip install flask flask-cors openai sqlalchemy python-dotenv
```

### Connection Failed (Red Dot)

**Check**:
1. Is backend running? (Terminal 1 should show "Running on http://127.0.0.1:5000")
2. Check browser console (F12) for errors
3. Try refreshing the page

### Slow Responses

**Normal**: GPT-5 responses take 20-40 seconds. This is expected.

**Too Slow** (>60 seconds):
- Check internet connection
- Check backend logs for errors

### CORS Errors

**Solution**: Make sure you're accessing via `http://localhost:8080`, not opening `index.html` directly

## Reporting Issues

When you find a bug or issue:

1. **Export Logs**: Click "Export Logs" button
2. **Take Screenshot**: Capture the error in the logs panel
3. **Note Details**:
   - What you typed
   - What response you got
   - What you expected
   - Response time
4. **Share**:
   - Exported JSON file
   - Screenshot
   - Description of issue

## Performance Benchmarks

Expected performance based on our tests:

| Metric | Expected Value |
|--------|---------------|
| Response Time | 20-40 seconds |
| Success Rate | 95%+ |
| Quality Score | 95%+ |
| Dialect Authenticity | Natural mixing of Arabic/French |
| Medical Safety | 100% (never gives medical advice) |
| CTA Presence | Present in booking-related queries |

If you see values significantly different from these, report it!

## Test Session Template

Use this template for organized testing:

```
Test Session: [Date/Time]
Tester: [Your Name]

Test 1: Greeting
Input: مرحبا
Response Time: ___s
Quality: [ ] Excellent [ ] Good [ ] Poor
Notes: _________________________________

Test 2: Price Question
Input: شحال prix تع séance?
Response Time: ___s
Quality: [ ] Excellent [ ] Good [ ] Poor
Notes: _________________________________

[Continue for all test cases...]

Overall Assessment:
- Connection Stable: [ ] Yes [ ] No
- Logs Clear: [ ] Yes [ ] No
- No Errors: [ ] Yes [ ] No
- Dialect Quality: [ ] Excellent [ ] Good [ ] Poor

Issues Found: _________________________________
```

## Questions?

- Check the logs first - they usually explain what's happening
- See detailed documentation in `frontend/README.md`
- See backend documentation in `README.md`
- Export logs and share with development team

## Happy Testing! 🚀

Remember: The chatbot is designed for **Tunisian dialect**, so test with natural Arabic/French mixing!
