// Configuration
const API_BASE_URL = 'https://laserostop-cm.loca.lt';

// State Management
const state = {
    messages: [],
    logs: [],
    stats: {
        totalMessages: 0,
        totalErrors: 0,
        totalTokens: 0,
        responseTimes: [],
        successCount: 0
    },
    filters: {
        frontend: true,
        backend: true,
        ai: true,
        error: true
    }
};

// Utility Functions
function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString('en-US', { hour12: false });
}

function formatDuration(ms) {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
}

function addLog(source, message, type = 'info', details = null) {
    const timestamp = getCurrentTime();
    const log = { timestamp, source, message, type, details };
    state.logs.push(log);

    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${source.toLowerCase()}`;
    if (type === 'error') logEntry.classList.add('error');

    logEntry.innerHTML = `
        <span class="log-timestamp">[${timestamp}]</span>
        <span class="log-source">[${source.toUpperCase()}]</span>
        <span class="log-message">${message}</span>
    `;

    if (details) {
        const detailsDiv = document.createElement('div');
        detailsDiv.className = 'log-details';
        detailsDiv.textContent = typeof details === 'object' ? JSON.stringify(details, null, 2) : details;
        logEntry.appendChild(detailsDiv);
    }

    const logContainer = document.getElementById('log-container');
    logContainer.appendChild(logEntry);
    logContainer.scrollTop = logContainer.scrollHeight;

    // Apply filters
    applyLogFilters();
}

function applyLogFilters() {
    const logEntries = document.querySelectorAll('.log-entry');
    logEntries.forEach(entry => {
        const isFiltered =
            (entry.classList.contains('frontend') && !state.filters.frontend) ||
            (entry.classList.contains('backend') && !state.filters.backend) ||
            (entry.classList.contains('ai') && !state.filters.ai) ||
            (entry.classList.contains('error') && !state.filters.error);

        if (isFiltered) {
            entry.classList.add('hidden');
        } else {
            entry.classList.remove('hidden');
        }
    });
}

function updateStats() {
    document.getElementById('stat-messages').textContent = state.stats.totalMessages;
    document.getElementById('stat-errors').textContent = state.stats.totalErrors;
    document.getElementById('stat-tokens').textContent = state.stats.totalTokens.toLocaleString();

    const avgTime = state.stats.responseTimes.length > 0
        ? state.stats.responseTimes.reduce((a, b) => a + b, 0) / state.stats.responseTimes.length
        : 0;
    document.getElementById('stat-response-time').textContent = formatDuration(Math.round(avgTime));

    const successRate = state.stats.totalMessages > 0
        ? ((state.stats.successCount / state.stats.totalMessages) * 100).toFixed(1)
        : 100;
    document.getElementById('stat-success-rate').textContent = `${successRate}%`;
}

function addMessage(role, content, metadata = {}) {
    const message = { role, content, timestamp: getCurrentTime(), metadata };
    state.messages.push(message);

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;

    const metaDiv = document.createElement('div');
    metaDiv.className = 'message-meta';

    let metaHTML = `<span class="message-timestamp">${message.timestamp}</span>`;

    if (metadata.tokens) {
        metaHTML += `<span class="message-tokens">📊 ${metadata.tokens} tokens</span>`;
    }
    if (metadata.responseTime) {
        metaHTML += `<span class="message-time">⏱️ ${formatDuration(metadata.responseTime)}</span>`;
    }
    if (metadata.ragUsed !== undefined) {
        metaHTML += `<span class="message-rag">${metadata.ragUsed ? '🔍 RAG used' : '❌ No RAG'}</span>`;
    }

    metaDiv.innerHTML = metaHTML;

    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(metaDiv);

    const chatMessages = document.getElementById('chat-messages');
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    addLog('FRONTEND', `${role === 'user' ? 'User' : 'Assistant'} message displayed (${content.length} chars)`);
}

function clearWelcomeMessage() {
    const welcome = document.querySelector('.welcome-message');
    if (welcome) {
        welcome.remove();
    }
}

async function checkBackendHealth() {
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');

    try {
        addLog('FRONTEND', 'Checking backend health...');

        const response = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Bypass-Tunnel-Reminder': 'true',
            }
        });

        if (response.ok) {
            const data = await response.json();
            statusIndicator.className = 'status-dot connected';
            statusText.textContent = 'Connected to Backend';
            addLog('BACKEND', 'Backend health check successful', 'info', data);
            return true;
        } else {
            throw new Error(`Backend returned status ${response.status}`);
        }
    } catch (error) {
        statusIndicator.className = 'status-dot error';
        statusText.textContent = 'Backend Offline';
        addLog('FRONTEND', `Backend health check failed: ${error.message}`, 'error');
        return false;
    }
}

async function sendMessage() {
    const input = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const useRAG = document.getElementById('use-rag').checked;
    const userId = document.getElementById('user-id').value.trim();
    const userText = input.value.trim();

    if (!userText) {
        addLog('FRONTEND', 'Attempted to send empty message', 'error');
        return;
    }

    // Disable input and button
    input.disabled = true;
    sendBtn.disabled = true;
    sendBtn.querySelector('.btn-text').style.display = 'none';
    sendBtn.querySelector('.btn-loading').style.display = 'inline';

    const startTime = Date.now();

    try {
        // Clear welcome message on first interaction
        clearWelcomeMessage();

        // Display user message
        addMessage('user', userText);
        addLog('FRONTEND', `User message sent: "${userText.substring(0, 50)}${userText.length > 50 ? '...' : ''}"`, 'info');

        // Clear input
        input.value = '';

        // Prepare request
        const requestBody = {
            user_text: userText,
            user_id: userId || undefined,
            use_rag: useRAG
        };

        addLog('FRONTEND', 'Sending request to backend API', 'info', {
            endpoint: `${API_BASE_URL}/chat`,
            body: requestBody
        });

        // Send to backend
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Bypass-Tunnel-Reminder': 'true',
            },
            body: JSON.stringify(requestBody)
        });

        const responseTime = Date.now() - startTime;

        addLog('BACKEND', `Received response from backend (${response.status})`, 'info', {
            status: response.status,
            statusText: response.statusText,
            responseTime: `${responseTime}ms`
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Backend error (${response.status}): ${errorText}`);
        }

        const data = await response.json();

        addLog('BACKEND', 'Response parsed successfully', 'info', {
            reply_length: data.reply?.length || 0,
            rag_used: data.rag_used,
            model: data.model_version
        });

        // Log AI/GPT details
        if (data.reply) {
            addLog('AI', 'GPT-5 generated response', 'info', {
                model: data.model_version,
                response_length: data.reply.length,
                rag_used: data.rag_used,
                rag_version: data.rag_version
            });
        }

        // Estimate tokens (rough approximation: 1 token ≈ 4 characters for mixed Arabic/English)
        const estimatedTokens = Math.ceil((userText.length + (data.reply?.length || 0)) / 4);

        // Display assistant message
        addMessage('assistant', data.reply, {
            responseTime,
            tokens: estimatedTokens,
            ragUsed: data.rag_used
        });

        // Update stats
        state.stats.totalMessages++;
        state.stats.successCount++;
        state.stats.responseTimes.push(responseTime);
        state.stats.totalTokens += estimatedTokens;
        updateStats();

        addLog('FRONTEND', 'Message exchange completed successfully', 'info', {
            responseTime: `${responseTime}ms`,
            tokens: estimatedTokens
        });

    } catch (error) {
        const responseTime = Date.now() - startTime;

        addLog('FRONTEND', `Error sending message: ${error.message}`, 'error', {
            error: error.toString(),
            stack: error.stack,
            responseTime: `${responseTime}ms`
        });

        addMessage('assistant', `❌ Error: ${error.message}`, {
            responseTime,
            tokens: 0
        });

        state.stats.totalMessages++;
        state.stats.totalErrors++;
        state.stats.responseTimes.push(responseTime);
        updateStats();

    } finally {
        // Re-enable input and button
        input.disabled = false;
        sendBtn.disabled = false;
        sendBtn.querySelector('.btn-text').style.display = 'inline';
        sendBtn.querySelector('.btn-loading').style.display = 'none';
        input.focus();
    }
}

function clearChat() {
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = `
        <div class="welcome-message">
            <h3>مرحبا بيك في LaserOstop! 👋</h3>
            <p>Test the chatbot by asking questions in Tunisian dialect (Derja).</p>
            <p><strong>Example questions:</strong></p>
            <ul>
                <li>شحال prix تع séance laser?</li>
                <li>نجم نعمل laser وأنا حامل؟</li>
                <li>Laser 3amel kifech?</li>
                <li>Nheb nhajer rendez-vous</li>
            </ul>
        </div>
    `;
    state.messages = [];
    addLog('FRONTEND', 'Chat cleared by user');
}

function clearLogs() {
    const logContainer = document.getElementById('log-container');
    logContainer.innerHTML = `
        <div class="log-entry frontend">
            <span class="log-timestamp">[${getCurrentTime()}]</span>
            <span class="log-source">[FRONTEND]</span>
            <span class="log-message">Logs cleared by user</span>
        </div>
    `;
    state.logs = [];
    addLog('FRONTEND', 'Log panel cleared');
}

function exportLogs() {
    addLog('FRONTEND', 'Exporting logs to file...');

    const logData = {
        exportedAt: new Date().toISOString(),
        stats: state.stats,
        messages: state.messages,
        logs: state.logs
    };

    const blob = new Blob([JSON.stringify(logData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `laserostop-logs-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    addLog('FRONTEND', 'Logs exported successfully', 'info', {
        filename: a.download,
        totalLogs: state.logs.length,
        totalMessages: state.messages.length
    });
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    addLog('FRONTEND', 'Testing interface initialized');
    addLog('FRONTEND', 'Checking backend connection...');

    // Check backend health
    checkBackendHealth();

    // Send button
    document.getElementById('send-btn').addEventListener('click', sendMessage);

    // Enter key to send
    document.getElementById('user-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Clear chat button
    document.getElementById('clear-chat').addEventListener('click', clearChat);

    // Clear logs button
    document.getElementById('clear-logs').addEventListener('click', clearLogs);

    // Export logs button
    document.getElementById('export-logs').addEventListener('click', exportLogs);

    // Log filter checkboxes
    ['frontend', 'backend', 'ai', 'error'].forEach(filter => {
        document.getElementById(`filter-${filter}`).addEventListener('change', (e) => {
            state.filters[filter] = e.target.checked;
            addLog('FRONTEND', `${filter.toUpperCase()} filter ${e.target.checked ? 'enabled' : 'disabled'}`);
            applyLogFilters();
        });
    });

    // Periodic health check (every 30 seconds)
    setInterval(checkBackendHealth, 30000);

    addLog('FRONTEND', 'All event listeners registered');
    addLog('FRONTEND', 'Ready to test chatbot! 🚀');
});
