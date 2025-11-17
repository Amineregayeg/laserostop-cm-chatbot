# LaserOstop CM Chatbot - Testing Interface

A comprehensive testing interface for the LaserOstop Community Manager Chatbot with full logging capabilities.

## Features

### 💬 Chat Interface
- Clean, user-friendly chat interface
- Support for Tunisian dialect (Arabic, French, Latin script)
- Real-time message display with timestamps
- Token usage and response time tracking

### 📊 Comprehensive Logging
The testing interface provides detailed logging for all system components:

- **Frontend Logs**: User interactions, UI events, API requests
- **Backend Logs**: API responses, status codes, processing times
- **AI/GPT Logs**: Model responses, RAG usage, generation details
- **Error Logs**: All errors with stack traces and context

### 🎯 Log Filtering
- Toggle visibility of different log sources
- Filter by: Frontend, Backend, AI, Errors
- Real-time log updates with auto-scroll

### 📈 Performance Statistics
- Total messages sent
- Average response time
- Success rate
- Error count
- Total tokens used

### 🔧 Testing Features
- RAG toggle (enable/disable RAG for comparison)
- Custom user ID for testing different users
- Export logs to JSON for analysis
- Clear chat and logs independently

## Quick Start

### Prerequisites
Make sure the Flask backend is running:
```bash
cd ..
python run.py
```

The backend should be running at `http://localhost:5000`.

### Running the Frontend

#### Option 1: Python HTTP Server
```bash
cd frontend
python -m http.server 8080
```

Then open: `http://localhost:8080`

#### Option 2: Node.js HTTP Server
```bash
cd frontend
npx http-server -p 8080
```

Then open: `http://localhost:8080`

#### Option 3: Direct File Access
Simply open `index.html` directly in your browser.

**Note**: If you get CORS errors with direct file access, use Option 1 or 2.

## Usage

### Testing the Chatbot

1. **Ensure Backend is Running**
   - Check the connection status indicator in the top-right
   - Green dot = connected, Red dot = offline

2. **Send a Test Message**
   - Type a message in Tunisian dialect
   - Press Enter or click "Send Message"
   - Watch the logs panel for detailed execution flow

3. **Monitor Logs**
   - All logs appear in real-time in the right panel
   - Use filters to focus on specific components
   - Check for errors highlighted in red

4. **Analyze Performance**
   - View statistics at the bottom of the page
   - Track response times, token usage, and success rate
   - Export logs for detailed analysis

### Example Test Questions

```
شحال prix تع séance laser?
(How much does a laser session cost?)

نجم نعمل laser وأنا حامل؟
(Can I do laser while pregnant?)

Laser 3amel kifech?
(How does laser work?)

Nheb nhajer rendez-vous
(I want to book an appointment)

Kifech naaref itha laser ynojem ywafek?
(How do I know if laser is suitable for me?)
```

## Log Types

### Frontend Logs (Blue)
- User input validation
- API request preparation
- UI state changes
- Error handling

### Backend Logs (Green)
- HTTP response codes
- Response parsing
- Backend processing time
- API endpoint information

### AI Logs (Purple)
- GPT model information
- Response generation details
- RAG usage status
- Token estimates

### Error Logs (Red)
- All errors with full context
- Stack traces
- Failed requests
- Validation errors

## Exporting Logs

Click "Export Logs" to download a JSON file containing:
- All log entries with timestamps
- Complete message history
- Performance statistics
- Error details

This is useful for:
- Debugging issues
- Performance analysis
- Sharing test results with the team
- Creating bug reports

## Configuration

Edit `app.js` to change the backend URL:
```javascript
const API_BASE_URL = 'http://localhost:5000';
```

For production deployment, update this to your production backend URL.

## Browser Compatibility

Tested and working on:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Troubleshooting

### Backend Connection Failed
- Ensure Flask backend is running on port 5000
- Check for CORS issues in browser console
- Verify API_BASE_URL in app.js

### CORS Errors
- Backend has CORS enabled by default
- If issues persist, serve frontend via HTTP server (not file://)

### Logs Not Appearing
- Check browser console for JavaScript errors
- Ensure log filters are enabled
- Try refreshing the page

## Development

### File Structure
```
frontend/
├── index.html      # Main HTML structure
├── styles.css      # All styling and animations
├── app.js          # Frontend logic and API integration
└── README.md       # This file
```

### Customization

**Colors**: Edit CSS variables in `styles.css`
**API Endpoints**: Modify `app.js` API calls
**UI Layout**: Update `index.html` structure

## Testing Checklist

Use this checklist when testing the chatbot:

- [ ] Backend connection successful (green indicator)
- [ ] Send message in Arabic script
- [ ] Send message in Latin script
- [ ] Send message with French/Arabic mix
- [ ] Test with RAG enabled
- [ ] Test with RAG disabled
- [ ] Verify all logs appear correctly
- [ ] Check response times are reasonable
- [ ] Test error handling (disconnect backend)
- [ ] Export logs successfully
- [ ] Clear chat and logs
- [ ] Test on different browsers

## Support

For issues or questions:
1. Check the logs for detailed error information
2. Export logs and share with the development team
3. Include browser console output if applicable
