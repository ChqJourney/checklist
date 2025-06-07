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
    
    // 使用 setTimeout 确保 DOM 更新后再滚动
    setTimeout(() => {
        logContent.scrollTop = logContent.scrollHeight;
    }, 0);
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
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
    `;    results.forEach((result, index) => {
        const statusClass = result.status === '完成' ? 'status-completed' : 'status-error';
        const displayPath = result.target_path ? result.target_path.substring(result.target_path.lastIndexOf('\\') + 1) : '未找到';
        
        tableHTML += `
            <tr>
                <td>${result.job_no}</td>
                <td>${result.job_creator}</td>
                <td>${result.engineers}</td>
                <td class="${statusClass}">${result.status}</td>
                <td title="${result.target_path || ''}">${result.target_path}</td>
                <td>
                    <div class="action-dropdown" data-target-path="${result.target_path || ''}">
                        <button class="action-btn" onclick="toggleDropdown(this)">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <circle cx="12" cy="12" r="1"></circle>
                                <circle cx="12" cy="5" r="1"></circle>
                                <circle cx="12" cy="19" r="1"></circle>
                            </svg>
                        </button>
                        <div class="dropdown-menu">
                            <button class="dropdown-item" onclick="openTargetFile(this)">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                    <polyline points="14,2 14,8 20,8"></polyline>
                                </svg>
                                打开文件
                            </button>
                            <button class="dropdown-item" onclick="openTargetFolder(this)">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2l5 0 2 3h9a2 2 0 0 1 2 2z"></path>
                                </svg>
                                打开目录
                            </button>
                        </div>
                    </div>
                </td>
            </tr>
        `;
    });
    
    tableHTML += '</tbody></table>';
    resultsContent.innerHTML = tableHTML;
}

// Dropdown菜单控制
function toggleDropdown(button) {
    const dropdown = button.nextElementSibling;
    const isOpen = dropdown.classList.contains('show');
    
    // 关闭所有其他的dropdown
    document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
        menu.classList.remove('show');
    });
    
    // 切换当前dropdown
    if (!isOpen) {
        // 计算按钮的位置
        const buttonRect = button.getBoundingClientRect();
        
        // 设置dropdown的位置为fixed，相对于视窗
        dropdown.style.top = (buttonRect.bottom + 2) + 'px';
        dropdown.style.left = (buttonRect.right - 120) + 'px'; // 120px是dropdown的宽度
        
        dropdown.classList.add('show');
    }
}

// 点击其他地方关闭dropdown
document.addEventListener('click', function(event) {
    if (!event.target.closest('.action-dropdown')) {
        document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
            menu.classList.remove('show');
        });
    }
});

// 打开target_path文件
async function openTargetFile(buttonElement) {
    const targetPath = buttonElement.closest('.action-dropdown').getAttribute('data-target-path');
    
    if (!targetPath) {
        addLog('目标路径为空，无法打开文件');
        return;
    }
    
    try {
        const result = await pywebview.api.open_target_file(targetPath);
        if (result.success) {
            addLog(`已打开文件: ${targetPath}`);
        } else {
            addLog(`打开文件失败: ${result.message || '未知错误'}`);
        }
    } catch (error) {
        addLog(`打开文件错误: ${error}`);
    }
    
    // 关闭dropdown
    document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
        menu.classList.remove('show');
    });
}

// 打开target_path所在目录
async function openTargetFolder(buttonElement) {
    const targetPath = buttonElement.closest('.action-dropdown').getAttribute('data-target-path');
    
    if (!targetPath) {
        addLog('目标路径为空，无法打开目录');
        return;
    }
    
    try {
        const result = await pywebview.api.open_target_folder(targetPath);
        if (result.success) {
            addLog(`已打开目录: ${targetPath}`);
        } else {
            addLog(`打开目录失败: ${result.message || '未知错误'}`);
        }
    } catch (error) {
        addLog(`打开目录错误: ${error}`);
    }
    
    // 关闭dropdown
    document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
        menu.classList.remove('show');
    });
}

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    addLog('界面加载完成，请选择文件开始处理');
    
});
