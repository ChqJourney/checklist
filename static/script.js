let isRunning = false;

async function selectFile() {
    try {
        const result = await pywebview.api.select_file();
        if (result.success) {
            document.getElementById('fileInfo').textContent = `已选择: ${result.filename}`;
            document.getElementById('runBtn').disabled = false;
            addLog(`文件选择成功: ${result.filename}`);
        } else {
            addLog(`文件选择失败: ${result.message || '未知错误'}`);
        }
    } catch (error) {
        addLog(`文件选择错误: ${error}`);
    }
}

async function runProcess() {
    if (isRunning) return;
    
    try {
        const result = await pywebview.api.process_tasks();
        if (!result.success) {
            addLog(`启动失败: ${result.message}`);
        }
    } catch (error) {
        addLog(`运行错误: ${error}`);
    }
}

function addLog(message) {
    const logContent = document.getElementById('logContent');
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    logEntry.textContent = message;
    logContent.appendChild(logEntry);
    logContent.scrollTop = logContent.scrollHeight;
}

function setRunning(running) {
    isRunning = running;
    const runBtn = document.getElementById('runBtn');
    runBtn.disabled = running;
    runBtn.textContent = running ? '运行中...' : '运行检查';
    if (running) {
        runBtn.classList.add('loading');
    } else {
        runBtn.classList.remove('loading');
    }
}

function updateResults(results) {
    const resultsContent = document.getElementById('resultsContent');
    
    if (!results || results.length === 0) {
        resultsContent.innerHTML = '<div class="empty-state">暂无结果数据</div>';
        return;
    }
    
    let tableHTML = `
        <table class="results-table">
            <thead>
                <tr>
                    <th>项目编号</th>
                    <th>创建者</th>
                    <th>工程师</th>
                    <th>状态</th>
                    <th>目录路径</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    results.forEach(result => {
        const statusClass = result.status === '完成' ? 'status-completed' : 'status-error';
        const displayPath = result.target_path ? result.target_path.substring(result.target_path.lastIndexOf('\\\\') + 1) : '未找到';
        
        tableHTML += `
            <tr>
                <td>${result.job_no}</td>
                <td>${result.job_creator}</td>
                <td>${result.engineers}</td>
                <td class="${statusClass}">${result.status}</td>
                <td title="${result.target_path || ''}">${displayPath}</td>
            </tr>
        `;
    });
    
    tableHTML += '</tbody></table>';
    resultsContent.innerHTML = tableHTML;
}

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    addLog('界面加载完成，请选择文件开始处理');
});
