// Voice Agent Dashboard JavaScript

// Tab switching
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');
    event.target.classList.add('active');
}

// Show status message
function showStatus(elementId, message, type) {
    const statusEl = document.getElementById(elementId);
    statusEl.textContent = message;
    statusEl.className = `status-message show ${type}`;

    // Auto-hide after 10 seconds
    setTimeout(() => {
        statusEl.classList.remove('show');
    }, 10000);
}

// Personal Message Form Handler
document.getElementById('personal-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);
    const submitBtn = e.target.querySelector('button[type="submit"]');

    submitBtn.disabled = true;
    submitBtn.textContent = 'Making Call...';

    try {
        const response = await fetch('/api/calls/personal-message', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            showStatus('personal-status',
                `Call initiated successfully! Call ID: ${data.call_id}`,
                'success'
            );
            e.target.reset();

            // Refresh call list after 2 seconds
            setTimeout(loadRecentCalls, 2000);
        } else {
            showStatus('personal-status',
                `Error: ${data.error}`,
                'error'
            );
        }
    } catch (error) {
        showStatus('personal-status',
            `Error: ${error.message}`,
            'error'
        );
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Make Call Now';
    }
});

// Facility Test Form Handler
document.getElementById('facility-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);
    const submitBtn = e.target.querySelector('button[type="submit"]');

    submitBtn.disabled = true;
    submitBtn.textContent = 'Making Test Call...';

    try {
        const response = await fetch('/api/calls/facility-test', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            showStatus('facility-status',
                `Test call initiated successfully! Call ID: ${data.call_id}`,
                'success'
            );
            e.target.reset();

            // Refresh call list after 2 seconds
            setTimeout(loadRecentCalls, 2000);
        } else {
            showStatus('facility-status',
                `Error: ${data.error}`,
                'error'
            );
        }
    } catch (error) {
        showStatus('facility-status',
            `Error: ${error.message}`,
            'error'
        );
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Make Test Call';
    }
});

// CSV Upload Form Handler
document.getElementById('csv-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);
    const submitBtn = e.target.querySelector('button[type="submit"]');

    submitBtn.disabled = true;
    submitBtn.textContent = 'Uploading...';

    try {
        const response = await fetch('/api/contacts/upload-csv', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            showStatus('csv-status',
                `Successfully uploaded ${data.imported_count} contacts! ${data.skipped_count > 0 ? `(${data.skipped_count} duplicates skipped)` : ''}`,
                'success'
            );
            e.target.reset();
        } else {
            showStatus('csv-status',
                `Error: ${data.error}`,
                'error'
            );
        }
    } catch (error) {
        showStatus('csv-status',
            `Error: ${error.message}`,
            'error'
        );
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Upload Contacts';
    }
});

// Load recent calls
async function loadRecentCalls() {
    const container = document.getElementById('recent-calls');

    try {
        const response = await fetch('/api/calls/recent');
        if (!response.ok) {
            // If endpoint doesn't exist yet, show placeholder
            container.innerHTML = '<p class="loading">No calls yet. Make your first call above!</p>';
            return;
        }

        const calls = await response.json();

        if (calls.length === 0) {
            container.innerHTML = '<p class="loading">No calls yet. Make your first call above!</p>';
            return;
        }

        container.innerHTML = calls.map(call => `
            <div class="call-item">
                <div class="call-item-header">
                    <div class="call-item-title">
                        ${call.contact_name} - ${formatCallType(call.call_type)}
                    </div>
                    <span class="call-status ${call.status}">
                        ${call.status.toUpperCase()}
                        ${call.test_result ? ` - ${call.test_result}` : ''}
                    </span>
                </div>
                <div class="call-item-details">
                    Phone: ${call.phone} |
                    Time: ${formatDate(call.created_at)} |
                    Duration: ${call.duration ? `${call.duration}s` : 'N/A'}
                </div>
                <div class="call-item-actions">
                    <button class="btn-small" onclick="viewTranscript(${call.id})">
                        View Transcript
                    </button>
                    ${call.recording_url ?
                        `<button class="btn-small" onclick="playRecording('${call.recording_url}')">
                            Play Recording
                        </button>` : ''
                    }
                </div>
            </div>
        `).join('');
    } catch (error) {
        container.innerHTML = '<p class="loading">No calls yet. Make your first call above!</p>';
    }
}

// View transcript
async function viewTranscript(callId) {
    try {
        const response = await fetch(`/api/calls/${callId}`);
        const data = await response.json();

        const modal = document.createElement('div');
        modal.className = 'transcript-modal show';
        modal.innerHTML = `
            <div class="transcript-content">
                <button class="transcript-close" onclick="this.closest('.transcript-modal').remove()">×</button>
                <h2>Call Transcript</h2>
                <p><strong>${data.contact.name}</strong> - ${data.contact.phone}</p>
                <p>Status: ${data.call.status} | Duration: ${data.call.duration || 'N/A'}s</p>
                ${data.call.test_result ? `<p>Test Result: <strong>${data.call.test_result}</strong></p>` : ''}
                <hr style="margin: 20px 0;">
                ${data.transcript.map(seg => `
                    <div class="transcript-segment ${seg.speaker}">
                        <div class="transcript-speaker">${seg.speaker}</div>
                        <div class="transcript-text">${seg.text}</div>
                    </div>
                `).join('')}
            </div>
        `;

        document.body.appendChild(modal);

        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    } catch (error) {
        alert('Error loading transcript: ' + error.message);
    }
}

// Play recording
function playRecording(url) {
    window.open(url, '_blank');
}

// Format helpers
function formatCallType(type) {
    return type.split('_').map(word =>
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000); // seconds

    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return date.toLocaleDateString();
}

// Load recent calls on page load
document.addEventListener('DOMContentLoaded', () => {
    loadRecentCalls();

    // Auto-refresh every 10 seconds
    setInterval(loadRecentCalls, 10000);
});
