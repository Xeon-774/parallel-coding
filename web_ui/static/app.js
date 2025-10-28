// Claude Orchestrator Dashboard v10.0 - Frontend Logic

// グローバル状態
let ws = null;
let reconnectTimeout = null;
let currentData = null;

// DOM要素
const elements = {
    connectionStatus: document.getElementById('connection-status'),
    lastUpdate: document.getElementById('last-update'),
    systemStatus: document.getElementById('system-status'),
    workersCount: document.getElementById('workers-count'),
    workspacePath: document.getElementById('workspace-path'),
    lastCheck: document.getElementById('last-check'),
    workersContainer: document.getElementById('workers-container'),
    logsContainer: document.getElementById('logs-container'),
    refreshLogsBtn: document.getElementById('refresh-logs'),
    clearLogsBtn: document.getElementById('clear-logs'),
    logFilter: document.getElementById('log-filter'),
    modal: document.getElementById('worker-modal')
};

// ========== WebSocket接続 ==========
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    console.log('Connecting to WebSocket:', wsUrl);

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('WebSocket connected');
        updateConnectionStatus(true);
        clearTimeout(reconnectTimeout);

        // 初期データを要求
        ws.send('get_status');

        // 定期的に更新を要求（5秒ごと）
        setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send('get_status');
            }
        }, 5000);
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log('Received data:', data);
            currentData = data;
            updateDashboard(data);
        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateConnectionStatus(false);
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected');
        updateConnectionStatus(false);

        // 5秒後に再接続を試みる
        reconnectTimeout = setTimeout(() => {
            console.log('Attempting to reconnect...');
            connectWebSocket();
        }, 5000);
    };
}

// ========== 接続ステータス更新 ==========
function updateConnectionStatus(connected) {
    if (connected) {
        elements.connectionStatus.textContent = '🟢 接続済み';
        elements.connectionStatus.classList.add('connected');
        elements.connectionStatus.classList.remove('disconnected');
    } else {
        elements.connectionStatus.textContent = '🔴 切断';
        elements.connectionStatus.classList.add('disconnected');
        elements.connectionStatus.classList.remove('connected');
    }
}

// ========== ダッシュボード更新 ==========
function updateDashboard(data) {
    // タイムスタンプ更新
    const now = new Date();
    elements.lastUpdate.textContent = formatTime(now);
    elements.lastCheck.textContent = formatTime(new Date(data.timestamp));

    // システム状態更新
    elements.systemStatus.textContent = data.status.toUpperCase();
    elements.systemStatus.style.color = data.status === 'running' ? 'var(--success-color)' : 'var(--text-muted)';

    elements.workersCount.textContent = data.workers_count;
    elements.workspacePath.textContent = data.workspace;

    // ワーカー一覧更新
    updateWorkers(data.workers);

    // ログ更新（オプション）
    if (data.latest_log) {
        loadLogs(data.latest_log);
    }
}

// ========== ワーカー一覧更新 ==========
function updateWorkers(workers) {
    if (!workers || workers.length === 0) {
        elements.workersContainer.innerHTML = `
            <div class="empty-state">
                <p>ワーカーが起動されるとここに表示されます</p>
            </div>
        `;
        return;
    }

    elements.workersContainer.innerHTML = workers.map(worker => `
        <div class="worker-card" onclick="showWorkerDetail('${worker.id}')">
            <div class="worker-header">
                <span class="worker-id">${worker.id}</span>
                <span class="worker-status ${worker.status}">${worker.status.toUpperCase()}</span>
            </div>
            <div class="worker-task">
                ${escapeHtml(worker.task || 'タスク読み込み中...')}
            </div>
            <div class="worker-output">
                ${escapeHtml(worker.recent_output || '出力待機中...')}
            </div>
            ${worker.screenshot ? `
                <div class="worker-screenshot">
                    <img src="/api/screenshots/${worker.screenshot}" alt="${worker.id} screenshot" loading="lazy">
                </div>
            ` : ''}
        </div>
    `).join('');
}

// ========== ワーカー詳細表示 ==========
async function showWorkerDetail(workerId) {
    const worker = currentData?.workers?.find(w => w.id === workerId);
    if (!worker) return;

    document.getElementById('modal-title').textContent = `${workerId} - 詳細`;
    document.getElementById('modal-task').textContent = worker.task || 'タスク情報なし';

    // 完全な出力を取得
    try {
        const response = await fetch(`/api/worker/${workerId}/output`);
        const data = await response.json();
        document.getElementById('modal-output').textContent = data.output || '出力なし';
    } catch (error) {
        document.getElementById('modal-output').textContent = 'エラー: 出力を取得できませんでした';
    }

    // スクリーンショット表示
    const screenshotContainer = document.getElementById('modal-screenshot');
    if (worker.screenshot) {
        screenshotContainer.innerHTML = `
            <img id="modal-screenshot-img" src="/api/screenshots/${worker.screenshot}" alt="${workerId} screenshot">
        `;
    } else {
        screenshotContainer.innerHTML = '<p>スクリーンショットなし</p>';
    }

    // モーダル表示
    elements.modal.classList.add('active');
}

// ========== ログ読み込み ==========
async function loadLogs(logFile) {
    try {
        const response = await fetch(`/api/logs/${logFile}`);
        const data = await response.json();

        if (data.logs && data.logs.length > 0) {
            displayLogs(data.logs);
        }
    } catch (error) {
        console.error('Failed to load logs:', error);
    }
}

// ========== ログ表示 ==========
function displayLogs(logs) {
    const filter = elements.logFilter.value;

    const filteredLogs = logs.filter(log => {
        if (filter === 'all') return true;
        return log.level?.toLowerCase() === filter;
    });

    elements.logsContainer.innerHTML = filteredLogs.map(log => {
        const level = log.level || 'info';
        const time = log.timestamp ? formatTime(new Date(log.timestamp)) : '--:--:--';
        const message = log.message || log.raw || 'No message';

        return `
            <div class="log-entry log-${level.toLowerCase()}">
                <span class="log-time">${time}</span>
                <span class="log-level">${level.toUpperCase()}</span>
                <span class="log-message">${escapeHtml(message)}</span>
            </div>
        `;
    }).join('');

    // 最新のログが見えるようにスクロール
    elements.logsContainer.scrollTop = elements.logsContainer.scrollHeight;
}

// ========== ユーティリティ関数 ==========
function formatTime(date) {
    return date.toTimeString().split(' ')[0];
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

// ========== イベントリスナー ==========
document.addEventListener('DOMContentLoaded', () => {
    // WebSocket接続開始
    connectWebSocket();

    // ログ更新ボタン
    elements.refreshLogsBtn.addEventListener('click', () => {
        if (currentData?.latest_log) {
            loadLogs(currentData.latest_log);
        }
    });

    // ログクリアボタン
    elements.clearLogsBtn.addEventListener('click', () => {
        elements.logsContainer.innerHTML = '<p class="empty-state">ログがクリアされました</p>';
    });

    // ログフィルター
    elements.logFilter.addEventListener('change', () => {
        if (currentData?.latest_log) {
            loadLogs(currentData.latest_log);
        }
    });

    // モーダルクローズ
    document.querySelector('.modal-close').addEventListener('click', () => {
        elements.modal.classList.remove('active');
    });

    // モーダル外クリックで閉じる
    elements.modal.addEventListener('click', (e) => {
        if (e.target === elements.modal) {
            elements.modal.classList.remove('active');
        }
    });
});

// ========== グローバル関数（HTMLから呼び出し可能） ==========
window.showWorkerDetail = showWorkerDetail;
