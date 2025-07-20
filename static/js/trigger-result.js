class LogViewer {
    constructor(logFile) {
        this.logFile = logFile;
        this.logVisible = false;
        this.streamVisible = false;
        this.streamSource = null;
        this.init();
    }

    init() {
        // Initialize event listeners
        document.getElementById('toggle-log-btn')?.addEventListener('click', () => this.toggleLog());
        document.getElementById('toggle-stream-btn')?.addEventListener('click', () => this.toggleStream());
    }

    toggleLog() {
        const logContent = document.getElementById('logContent');
        const toggleBtn = document.getElementById('toggle-log-btn');
        
        if (this.logVisible) {
            logContent.style.display = 'none';
            logContent.textContent = '';
            toggleBtn.textContent = '🔗 View Log File';
            this.logVisible = false;
        } else {
            logContent.textContent = 'Loading...';
            logContent.style.display = 'block';
            toggleBtn.textContent = '🔗 Hide Log File';
            
            fetch(`/logs/${this.logFile}`)
                .then(res => {
                    if (!res.ok) throw new Error('Failed to load log.');
                    return res.text();
                })
                .then(data => {
                    logContent.textContent = data;
                    this.logVisible = true;
                })
                .catch(err => {
                    logContent.textContent = `❌ ${err.message}`;
                    this.logVisible = true;
                });
        }
    }

    toggleStream() {
        const streamContent = document.getElementById('streamContent');
        const toggleBtn = document.getElementById('toggle-stream-btn');

        if (this.streamVisible) {
            if (this.streamSource) {
                this.streamSource.close();
                this.streamSource = null;
            }
            streamContent.style.display = 'none';
            streamContent.textContent = 'Waiting for updates...';
            toggleBtn.textContent = '🔄 Stream Log (Real-time)';
            this.streamVisible = false;
        } else {
            streamContent.innerHTML = '';
            streamContent.style.display = 'block';
            toggleBtn.textContent = '🛑 Stop Stream';

            this.streamSource = new EventSource(`/stream-log?file=${this.logFile}`);
            
            this.streamSource.onmessage = (event) => {
                streamContent.textContent += event.data + '\n';
                streamContent.scrollTop = streamContent.scrollHeight;
            };
            
            this.streamSource.onerror = () => {
                streamContent.textContent += '\n❌ Stream stopped.';
                if (this.streamSource) {
                    this.streamSource.close();
                    this.streamSource = null;
                }
                this.streamVisible = false;
                toggleBtn.textContent = '🔄 Stream Log (Real-time)';
            };

            this.streamVisible = true;
        }
    }
}

// Global initialization
document.addEventListener('DOMContentLoaded', () => {
    const logFile = window.logFileFromTemplate;
    if (logFile) {
        new LogViewer(logFile);
    }
});
