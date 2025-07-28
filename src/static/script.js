let isRunning = false;
let isLogPanelCollapsed = false;

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
    try {
        const result = await pywebview.api.process_tasks();
        if (!result.success) {
            addLog(`操作失败: ${result.message}`);
        } else {
            if (result.message === '已请求取消') {
                addLog('正在取消任务处理...');
            }
        }
    } catch (error) {
        addLog(`运行错误: ${error}`);
    }
}

function addLog(message) {
    addLogWithLevel(message, 'INFO');
}

function addLogWithLevel(message, level) {
    const logContent = document.getElementById('logContent');
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-${level.toLowerCase()}`;
    
    // 获取日志级别的配置（颜色和图标）
    const levelConfig = getLogLevelConfig(level);
    
    // 创建日志内容
    const timestamp = new Date().toLocaleTimeString();
    const escapedMessage = escapeHtml(message);
    const isLongMessage = message.length > 150;
    
    if (isLongMessage) {
        const shortMessage = escapeHtml(message.substring(0, 150) + '...');
        logEntry.innerHTML = `
            <span class="log-timestamp">${timestamp}</span>
            <span class="log-level" style="color: ${levelConfig.color}">${levelConfig.icon} ${level}</span>
            <span class="log-message">
                <span class="message-short">${shortMessage}</span>
                <span class="message-full" style="display: none;">${escapedMessage}</span>
                <button class="expand-btn" onclick="toggleMessage(this)" style="
                    background: none; 
                    border: none; 
                    color: #007bff; 
                    cursor: pointer; 
                    font-size: 11px;
                    margin-left: 5px;
                    text-decoration: underline;
                ">展开</button>
            </span>
        `;
    } else {
        logEntry.innerHTML = `
            <span class="log-timestamp">${timestamp}</span>
            <span class="log-level" style="color: ${levelConfig.color}">${levelConfig.icon} ${level}</span>
            <span class="log-message">${escapedMessage}</span>
        `;
    }
    
    logContent.appendChild(logEntry);
    
    // 限制日志数量，避免内存占用过多
    const maxLogs = 1000;
    while (logContent.children.length > maxLogs) {
        logContent.removeChild(logContent.firstChild);
    }
    
    // 使用 setTimeout 确保 DOM 更新后再滚动
    setTimeout(() => {
        logContent.scrollTop = logContent.scrollHeight;
    }, 0);
}

function getLogLevelConfig(level) {
    const configs = {
        'DEBUG': { color: '#6c757d', icon: '🔍' },
        'INFO': { color: '#17a2b8', icon: 'ℹ️' },
        'WARNING': { color: '#ffc107', icon: '⚠️' },
        'ERROR': { color: '#dc3545', icon: '❌' },
        'CRITICAL': { color: '#6f42c1', icon: '🚨' }
    };
    return configs[level] || configs['INFO'];
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncateMessage(message, maxLength = 200) {
    if (message.length <= maxLength) {
        return message;
    }
    return message.substring(0, maxLength) + '...';
}

async function clearLogs() {
    try {
        const result = await pywebview.api.clear_logs();
        if (result.success) {
            const logContent = document.getElementById('logContent');
            logContent.innerHTML = '<div class="log-entry">日志已清除</div>';
        } else {
            console.error('清除日志失败:', result.message);
        }
    } catch (error) {
        console.error('清除日志错误:', error);
        // 如果API调用失败，直接清除前端显示
        const logContent = document.getElementById('logContent');
        logContent.innerHTML = '<div class="log-entry">日志已清除</div>';
    }
}

function setRunning(running) {
    isRunning = running;
    const runBtn = document.getElementById('runBtn');
    
    if (running) {
        runBtn.disabled = false; // 运行时启用按钮以便取消
        runBtn.textContent = '取消';
        runBtn.classList.add('loading');
        runBtn.classList.add('cancel-mode');
    } else {
        runBtn.disabled = true; // 停止时禁用按钮，直到选择文件
        runBtn.textContent = '运行';
        runBtn.classList.remove('loading');
        runBtn.classList.remove('cancel-mode');
    }
}
function deSelectedTaskFile(){
    document.getElementById('fileInfo').textContent = `请选取任务清单文件`;
    const runBtn = document.getElementById('runBtn');
    runBtn.disabled = true;
    runBtn.textContent = '运行';
    runBtn.classList.remove('loading');
    runBtn.classList.remove('cancel-mode');
}

function updateResults(results) {
    const resultsContent = document.getElementById('resultsContent');
    const efillingBtn = document.getElementById('efillingBtn');
    
    if (!results || results.length === 0) {
        resultsContent.innerHTML = '<div class="empty-state">暂无结果数据</div>';
        // 隐藏E-filing按钮
        if (efillingBtn) {
            efillingBtn.style.display = 'none';
        }
        return;
    }
    
    // 显示E-filing按钮
    if (efillingBtn) {
        efillingBtn.style.display = 'inline-flex';
    }
    
      let tableHTML = `
        <table class="results-table">
            <thead>
                <tr>
                    <th>项目编号</th>
                    <th>客服</th>
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
                <td title="${result.target_path || ''}">${result.target_path ?? ""}</td>
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

// 展开和收起日志消息
function toggleMessage(button) {
    const messageContainer = button.parentElement;
    const shortMessage = messageContainer.querySelector('.message-short');
    const fullMessage = messageContainer.querySelector('.message-full');
    
    if (shortMessage.style.display !== 'none') {
        // 展开消息
        shortMessage.style.display = 'none';
        fullMessage.style.display = 'inline';
        button.textContent = '收起';
    } else {
        // 收起消息
        shortMessage.style.display = 'inline';
        fullMessage.style.display = 'none';
        button.textContent = '展开';
    }
}

// 收缩/展开日志面板
function toggleLogPanel() {
    const logPanel = document.getElementById('logPanel');
    const toggleIcon = document.querySelector('.toggle-icon');
    
    isLogPanelCollapsed = !isLogPanelCollapsed;
    
    if (isLogPanelCollapsed) {
        logPanel.classList.add('collapsed');
    } else {
        logPanel.classList.remove('collapsed');
    }
    
    // 保存状态到localStorage
    localStorage.setItem('logPanelCollapsed', isLogPanelCollapsed);
}

// Base Directory 相关功能
let currentBaseDir = '';

async function initializeBaseDir(retryCount = 0) {
    try {
        console.log(`开始初始化配置... (尝试 ${retryCount + 1}/6)`);
        
        // 检查 pywebview.api 是否可用
        if (typeof pywebview === 'undefined' || !pywebview.api) {
            console.log('pywebview.api 不可用');
            
            // 检查是否还能重试 (最多重试5次)
            if (retryCount < 5) {
                console.log('将在 1 秒后重试...');
                setTimeout(() => initializeBaseDir(retryCount + 1), 1000);
                return;
            } else {
                console.log('重试次数已达上限，使用默认配置');
                addLog('配置初始化失败，已加载默认配置');
                return;
            }
        }
        
        const result = await pywebview.api.get_all_config();
        console.log('API调用结果:', result);
        
        if (result.success) {
            currentConfig = result.config;
            currentBaseDir = currentConfig.base_dir || '';
            console.log('成功获取配置:', currentConfig);
            updateBaseDirTooltip(currentConfig);
            addLog('配置初始化成功');
        } else {
            console.log('获取配置失败:', result.message);
            addLog(`获取配置失败: ${result.message}`);
            
            // 不管成功失败，都重试5次
            if (retryCount < 5) {
                console.log('将在 1 秒后重试...');
                setTimeout(() => initializeBaseDir(retryCount + 1), 1000);
            } else {
                console.log('重试次数已达上限');
                addLog('配置初始化重试次数已达上限');
            }
        }
    } catch (error) {
        console.error('获取配置异常:', error);
        addLog(`获取配置失败: ${error}`);
        
        // 不管成功失败，都重试5次
        if (retryCount < 5) {
            console.log('将在 1 秒后重试...');
            setTimeout(() => initializeBaseDir(retryCount + 1), 1000);
        } else {
            console.log('重试次数已达上限');
            addLog('配置初始化重试次数已达上限');
        }
    }
}

function updateBaseDirTooltip(config) {
    const tooltip = document.getElementById('baseDirTooltip');
    if (tooltip) {
        const team = config.team || 'general';
        const baseDir = config.base_dir || '未设置';
        const checklist = config.checklist || 'cover';

        const displayText = `<div>Team: ${team === 'general' ? 'General' : 'PPT'} </div><div>基础目录:  ${baseDir} </div><div>模式: ${checklist === 'cover' ? '覆盖' : '填写'}</div>`;
        tooltip.innerHTML = displayText;
        console.log('更新tooltip:', displayText);
    } else {
        console.error('未找到baseDirTooltip元素');
    }
}

// 配置相关函数
let currentConfig = {
    team: 'general',
    base_dir: '',
    checklist: 'cover',
    task_list_map: {
        job_no: 0,
        job_creator: 1,
        engineers: 2
    },
    efilling_tool_path: ''
};

async function openConfigModal() {
    try {
        // 获取当前配置
        const result = await pywebview.api.get_all_config();
        if (result.success) {
            currentConfig = result.config;
            populateConfigModal(currentConfig);
            document.getElementById('configModal').classList.add('show');
        } else {
            addLog(`获取配置失败: ${result.message || '未知错误'}`);
        }
    } catch (error) {
        addLog(`获取配置错误: ${error}`);
        // 使用默认配置
        populateConfigModal(currentConfig);
        document.getElementById('configModal').classList.add('show');
    }
}

function populateConfigModal(config) {
    // 设置团队选择
    document.getElementById('teamSelect').value = config.team || 'general';
    
    // 设置基础目录
    document.getElementById('currentBaseDir').value = config.base_dir || '';
    
    // 设置检查清单模式
    const checklistValue = config.checklist || 'cover';
    const checklistRadio = document.querySelector(`input[name="checklist"][value="${checklistValue}"]`);
    if (checklistRadio) {
        checklistRadio.checked = true;
    }
    
    // 设置任务列表映射
    const taskMap = config.task_list_map || { job_no: 0, job_creator: 1, engineers: 2 };
    document.getElementById('mapJobNo').value = (taskMap.job_no || 0) + 1;
    document.getElementById('mapJobCreator').value = (taskMap.job_creator || 1) + 1;
    document.getElementById('mapEngineers').value = (taskMap.engineers || 2) + 1;
    
    // 设置E-filing工具路径
    document.getElementById('efillingToolPath').value = config.efilling_tool_path || '';
}

function closeConfigModal() {
    document.getElementById('configModal').classList.remove('show');
}

async function selectFolder() {
    try {
        const result = await pywebview.api.select_folder();
        if (result.success) {
            document.getElementById('currentBaseDir').value = result.path;
            addLog(`已选择文件夹: ${result.path}`);
        } else {
            addLog(`文件夹选择失败: ${result.message || '未知错误'}`);
        }
    } catch (error) {
        addLog(`文件夹选择错误: ${error}`);
    }
}

async function saveAllConfig() {
    try {
        // 收集所有配置数据
        const newConfig = {
            team: document.getElementById('teamSelect').value,
            base_dir: document.getElementById('currentBaseDir').value,
            checklist: document.querySelector('input[name="checklist"]:checked')?.value || 'cover',
            task_list_map: {
                job_no: (parseInt(document.getElementById('mapJobNo').value) || 1) - 1,
                job_creator: (parseInt(document.getElementById('mapJobCreator').value) || 2) - 1,
                engineers: (parseInt(document.getElementById('mapEngineers').value) || 3) - 1
            },
            efilling_tool_path: document.getElementById('efillingToolPath').value || ''
        };
        
        // 验证必填项
        if (!newConfig.team) {
            addLog('错误: 请选择团队');
            return;
        }
        
        if (!newConfig.base_dir) {
            addLog('错误: 请设置基础目录');
            return;
        }
        // 验证task_list_map的数值是否合理
        if (isNaN(newConfig.task_list_map.job_no) || newConfig.task_list_map.job_no < 0) {
            addLog('错误: 任务编号映射必须是非负整数');
            return;
        }

        if (isNaN(newConfig.task_list_map.job_creator) || newConfig.task_list_map.job_creator < 0) {
            addLog('错误: 客服映射必须是非负整数');
            return;
        }

        if (isNaN(newConfig.task_list_map.engineers) || newConfig.task_list_map.engineers < 0) {
            addLog('错误: 工程师映射必须是非负整数');
            return;
        }

        // 保存配置
        const result = await pywebview.api.save_all_config(newConfig);
        if (result.success) {
            currentConfig = newConfig;
            updateBaseDirTooltip(currentConfig);
            closeConfigModal();
            addLog('配置保存成功');
            
            // 如果有已选择的文件，重新验证
            const fileInfo = document.getElementById('fileInfo').textContent;
            if (fileInfo && !fileInfo.includes('请选取')) {
                deSelectedTaskFile();
                addLog('配置已更新，请重新选择任务列表文件');
            }
        } else {
            addLog(`保存配置失败: ${result.message || '未知错误'}`);
        }
    } catch (error) {
        addLog(`保存配置错误: ${error}`);
    }
}

// 兼容旧的函数名（保持向后兼容）
async function selectBaseDir() {
    await openConfigModal();
}

async function closeBaseDirModal() {
    closeConfigModal();
}

async function saveBaseDir() {
    await saveAllConfig();
}

// 点击modal外部关闭
document.addEventListener('click', function(event) {
    const modal = document.getElementById('configModal');
    if (event.target === modal) {
        closeConfigModal();
    }
});

// ESC键关闭modal
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeConfigModal();
    }
});

// 页面加载时恢复日志面板状态
document.addEventListener('DOMContentLoaded', function() {
    const saved = localStorage.getItem('logPanelCollapsed');
    if (saved === 'true') {
        toggleLogPanel();
    }
    
    addLog('界面加载完成，请选择文件开始处理');
    
    // 初始化配置
    initializeBaseDir();
});

// 选择exe文件
async function selectExeFile() {
    try {
        const result = await pywebview.api.select_exe_file();
        if (result.success) {
            document.getElementById('efillingToolPath').value = result.path;
            addLog(`已选择E-filing工具: ${result.path}`);
        } else {
            addLog(`E-filing工具选择失败: ${result.message || '未知错误'}`);
        }
    } catch (error) {
        addLog(`E-filing工具选择错误: ${error}`);
    }
}

// 打开E-filing工具
async function openEfillingTool() {
    try {
        const result = await pywebview.api.open_efiling_tool();
        if (result.success) {
            addLog('E-filing工具启动成功');
        } else {
            addLog(`启动E-filing工具失败: ${result.message || '未知错误'}`);
        }
    } catch (error) {
        addLog(`启动E-filing工具错误: ${error}`);
    }
}
