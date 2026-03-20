// 全局变量保存请求数据
        let allRequests = [];
        let traceSocket = null;
        let traceReconnectTimer = null;
        
        document.addEventListener('DOMContentLoaded', function() {
            const loadingEl = document.getElementById('loading');
            const errorEl = document.getElementById('error');
            const requestListEl = document.getElementById('request-list');
            const emptyStateEl = document.getElementById('empty-state');
            const defaultStateEl = document.getElementById('default-state');
            const detailContentEl = document.getElementById('detail-content');
            const searchInputEl = document.getElementById('search-input');
            const methodFilterEl = document.getElementById('method-filter');
            const statusFilterEl = document.getElementById('status-filter');
            const urlFilterEl = document.getElementById('url-filter');
            
            // 全局变量
            window.currentRequestId = null;
            window.currentTagFilter = null; // 当前选中的tag筛选
            
            const escapeHtml = (value) => {
                if (value === null || value === undefined) return '';
                return String(value)
                    .replace(/&/g, '&amp;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;')
                    .replace(/"/g, '&quot;')
                    .replace(/'/g, '&#39;');
            };
            
            const prettyJson = (value) => {
                if (!value) {
                    return '';
                }
                try {
                    const parsed = JSON.parse(value);
                    return JSON.stringify(parsed, null, 2);
                } catch {
                    return value;
                }
            };

            const escapeForShell = (value) => {
                return String(value || '')
                    .replace(/\\/g, '\\\\')
                    .replace(/"/g, '\\"');
            };

            function generateCurlCommand(traceData) {
                // Build a shell-friendly cURL command from whatever metadata we store
                const method = (traceData.method || 'GET').toUpperCase();
                const parts = ['curl'];

                if (method !== 'GET') {
                    parts.push(`-X ${method}`);
                }

                const headers = traceData.headers || {};
                Object.entries(headers).forEach(([name, value]) => {
                    const headerValue = value ?? '';
                    parts.push(`-H "${escapeForShell(name)}: ${escapeForShell(headerValue)}"`);
                });

                const body =
                    traceData.body ??
                    traceData.request_body ??
                    traceData.data ??
                    '';

                if (body) {
                    parts.push(`-d "${escapeForShell(body)}"`);
                }

                const url = traceData.url || traceData.request_url || '';
                parts.push(`"${url}"`);

                return parts.join(' ');
            }

            const copyTextToClipboard = (text) => {
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    return navigator.clipboard.writeText(text);
                }

                return new Promise((resolve, reject) => {
                    const textarea = document.createElement('textarea');
                    textarea.value = text;
                    textarea.style.position = 'fixed';
                    textarea.style.top = '-9999px';
                    document.body.appendChild(textarea);
                    textarea.focus();
                    textarea.select();

                    try {
                        document.execCommand('copy');
                        resolve();
                    } catch (err) {
                        reject(err);
                    } finally {
                        document.body.removeChild(textarea);
                    }
                });
            };

            const handleCopyButtonClick = async (event) => {
                event.stopPropagation();
                const button = event.currentTarget;
                const traceId = Number(button.dataset.id);
                const trace = allRequests.find(item => item.id === traceId);
                if (!trace) {
                    return;
                }

                // Copy cURL string with both headers and body injected
                const curlCommand = generateCurlCommand(trace);
                const originalText = button.textContent;
                try {
                    await copyTextToClipboard(curlCommand);
                    button.textContent = 'Copied!';
                } catch (err) {
                    console.error('Copy cURL failed', err);
                    button.textContent = 'Copy failed';
                } finally {
                    setTimeout(() => {
                        button.textContent = originalText;
                    }, 1500);
                }
            };

            const attachCurlButtons = () => {
                // Ensure every new list item wires up the copy action without duplicates
                const curlButtons = requestListEl.querySelectorAll('.copy-curl-btn');
                curlButtons.forEach(button => {
                    button.removeEventListener('click', handleCopyButtonClick);
                    button.addEventListener('click', handleCopyButtonClick);
                });
            };
            
            // 获取方法对应的 CSS 类名
            function getMethodClass(method) {
                const methodLower = method.toLowerCase();
                switch(methodLower) {
                    case 'get': return 'method-get';
                    case 'post': return 'method-post';
                    case 'put': return 'method-put';
                    case 'delete': return 'method-delete';
                    case 'patch': return 'method-patch';
                    default: return 'method-get';
                }
            }
            
            // 获取状态码对应的 CSS 类名
            function getStatusCodeClass(statusCode) {
                if (statusCode >= 200 && statusCode < 300) return 'status-2xx';
                if (statusCode >= 400 && statusCode < 500) return 'status-4xx';
                if (statusCode >= 500) return 'status-5xx';
                return '';
            }
            
            // 创建请求项 HTML（时间线视图）
            function createRequestItem(request, index) {
                const methodClass = getMethodClass(request.method);
                const statusClass = getStatusCodeClass(request.status_code);
                
                // 提取时间部分（如 "12:00:01"）
                let timeStr = '';
                if (request.created_at) {
                    // 从 "2026-03-19 18:51:07" 中提取时间部分
                    const parts = request.created_at.split(' ');
                    if (parts.length > 1) {
                        timeStr = parts[1]; // 获取时间部分
                    } else {
                        timeStr = request.created_at;
                    }
                }
                
                // 处理tags显示
                let tagsHtml = '';
                if (request.tags && request.tags.trim()) {
                    const tags = request.tags.split(',').map(tag => tag.trim()).filter(tag => tag);
                    if (tags.length > 0) {
                        tagsHtml = `
                            <div class="timeline-tags">
                                ${tags.map(tag => `<span class="tag" data-tag="${tag}">${tag}</span>`).join('')}
                            </div>
                        `;
                    }
                }
                
                return `
                    <div class="request-item timeline-item" data-id="${request.id}" data-index="${index}">
                        <span class="timeline-time">${timeStr}</span>
                        <span class="timeline-method ${methodClass}">${request.method}</span>
                        <span class="timeline-url">${request.url}</span>
                        <span class="timeline-status ${statusClass}">${request.status_code}</span>
                        ${tagsHtml}
                        <div class="request-actions">
                            <button type="button" class="copy-curl-btn" data-id="${request.id}">
                                Copy as cURL
                            </button>
                        </div>
                    </div>
                `;
            }
            
            // 显示错误
            function showError(message) {
                loadingEl.style.display = 'none';
                errorEl.textContent = message || '加载数据时出错，请检查后端服务是否运行。';
                errorEl.style.display = 'block';
            }
            
            // 显示空状态
            function showEmptyState() {
                loadingEl.style.display = 'none';
                emptyStateEl.style.display = 'block';
            }
            
            // 筛选请求数据
            function filterRequests(requests) {
                if (!requests || requests.length === 0) {
                    return [];
                }
                
                // 获取筛选条件
                const methodFilter = methodFilterEl.value;
                const statusFilter = statusFilterEl.value;
                const urlFilter = urlFilterEl.value.toLowerCase().trim();
                const searchTerm = (searchInputEl && searchInputEl.value || '').toLowerCase().trim();
                
                // 筛选请求
                return requests.filter(request => {
                    // Method筛选
                    if (methodFilter !== 'all' && request.method !== methodFilter) {
                        return false;
                    }
                    
                    // Status筛选
                    if (statusFilter !== 'all' && String(request.status_code) !== statusFilter) {
                        return false;
                    }
                    
                    // URL筛选
                    if (urlFilter && !request.url.toLowerCase().includes(urlFilter)) {
                        return false;
                    }

                    // Search 快速匹配 URL 或状态码
                    if (searchTerm) {
                        const matchesUrl = request.url && request.url.toLowerCase().includes(searchTerm);
                        const matchesStatus = String(request.status_code).includes(searchTerm);
                        if (!matchesUrl && !matchesStatus) {
                            return false;
                        }
                    }
                    
                    // Tag筛选
                    if (window.currentTagFilter) {
                        // 检查请求是否包含当前选中的tag
                        if (!request.tags || !request.tags.trim()) {
                            return false;
                        }
                        
                        const tags = request.tags.split(',').map(tag => tag.trim());
                        if (!tags.includes(window.currentTagFilter)) {
                            return false;
                        }
                    }
                    
                    return true;
                });
            }
            
            // 应用筛选并刷新显示
            function applyFilter() {
                if (!allRequests || allRequests.length === 0) {
                    return;
                }
                
                const filteredRequests = filterRequests(allRequests);
                
                if (filteredRequests.length === 0) {
                    // 显示空状态
                    requestListEl.style.display = 'none';
                    emptyStateEl.style.display = 'block';
                    
                    // 重置选中状态
                    window.currentRequestId = null;
                    document.getElementById('replay-btn').disabled = true;
                    defaultStateEl.style.display = 'block';
                    detailContentEl.style.display = 'none';
                    return;
                }
                
                // 生成筛选后的请求项 HTML
                const itemsHtml = filteredRequests.map((request, index) => createRequestItem(request, index)).join('');
                requestListEl.innerHTML = itemsHtml;
                requestListEl.style.display = 'block';
                emptyStateEl.style.display = 'none';
                
                // 检查当前选中的请求是否在筛选结果中
                let selectedRequestInFilter = null;
                if (window.currentRequestId) {
                    selectedRequestInFilter = filteredRequests.find(request => request.id === window.currentRequestId);
                }
                
                // 为每个请求项添加点击事件
                const requestItems = requestListEl.querySelectorAll('.request-item');
                requestItems.forEach(item => {
                    item.addEventListener('click', function() {
                        // 移除其他项的选中状态
                        requestItems.forEach(i => i.classList.remove('selected'));
                        // 添加当前项的选中状态
                        this.classList.add('selected');
                        
                        // 获取请求索引
                        const index = parseInt(this.getAttribute('data-index'));
                        const request = filteredRequests[index];
                        
                        // 显示请求详情
                        showRequestDetail(request);
                    });
                    
                    // 如果当前选中的请求在筛选结果中，标记为选中
                    const itemId = parseInt(item.getAttribute('data-id'));
                    if (selectedRequestInFilter && itemId === selectedRequestInFilter.id) {
                        item.classList.add('selected');
                    }
                });
                attachCurlButtons();
                
                // 如果当前选中的请求不在筛选结果中，重置选中状态
                if (!selectedRequestInFilter) {
                    window.currentRequestId = null;
                    document.getElementById('replay-btn').disabled = true;
                    defaultStateEl.style.display = 'block';
                    detailContentEl.style.display = 'none';
                }
                
                // 自动滚动到底部，显示最新请求
                setTimeout(() => {
                    requestListEl.scrollTop = requestListEl.scrollHeight;
                }, 100);
                
                // 为tag元素添加点击事件
                const tagElements = requestListEl.querySelectorAll('.tag');
                tagElements.forEach(tag => {
                    tag.addEventListener('click', function(e) {
                        e.stopPropagation(); // 阻止事件冒泡，避免触发请求项的点击事件
                        
                        const tagValue = this.getAttribute('data-tag');
                        
                        // 如果点击的是当前已选中的tag，则取消筛选
                        if (window.currentTagFilter === tagValue) {
                            window.currentTagFilter = null;
                            this.classList.remove('active');
                        } else {
                            // 否则，设置新的tag筛选
                            window.currentTagFilter = tagValue;
                            
                            // 移除所有tag的active状态
                            tagElements.forEach(t => t.classList.remove('active'));
                            // 为当前点击的tag添加active状态
                            this.classList.add('active');
                        }
                        
                        // 应用筛选
                        applyFilter();
                    });
                    
                    // 如果当前有tag筛选，标记对应的tag为active状态
                    if (window.currentTagFilter && tag.getAttribute('data-tag') === window.currentTagFilter) {
                        tag.classList.add('active');
                    }
                });
            }
            
            // 显示请求列表
            function showRequestList(requests) {
                loadingEl.style.display = 'none';
                
                if (!requests || requests.length === 0) {
                    showEmptyState();
                    return;
                }
                
                // 保存到全局变量
                allRequests = requests;
                
                // 应用筛选显示
                applyFilter();
            }
            
            // 显示请求详情
            function showRequestDetail(request) {
                // 隐藏默认状态
                defaultStateEl.style.display = 'none';

                const requestBodyRaw = request.request_body || '';
                const responseBodyRaw = request.response_body || '';
                const requestBodySection = requestBodyRaw
                    ? `<pre class="detail-code"><code class="language-json">${escapeHtml(prettyJson(requestBodyRaw))}</code></pre>`
                    : '<div class="detail-value">(空)</div>';
                const responseBodySection = responseBodyRaw
                    ? `<pre class="detail-code"><code class="language-json">${escapeHtml(prettyJson(responseBodyRaw))}</code></pre>`
                    : '<div class="detail-value">(空)</div>';

                const detailHtml = `
                    <div class="detail-item">
                        <span class="detail-label">请求方法</span>
                        <div class="detail-value">${escapeHtml(request.method)}</div>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">请求URL</span>
                        <div class="detail-value">${escapeHtml(request.url)}</div>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">状态码</span>
                        <div class="detail-value">${escapeHtml(request.status_code)}</div>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">请求体</span>
                        ${requestBodySection}
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">响应体</span>
                        ${responseBodySection}
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">创建时间</span>
                        <div class="detail-value">${escapeHtml(request.created_at)}</div>
                    </div>
                `;

                detailContentEl.innerHTML = detailHtml;
                detailContentEl.style.display = 'block';

                const codeBlocks = detailContentEl.querySelectorAll('code.language-json');
                if (window.Prism && Prism.highlightElement) {
                    codeBlocks.forEach(block => Prism.highlightElement(block));
                }

                // 显示Replay按钮区域
                const replaySectionEl = document.getElementById('replay-section');
                replaySectionEl.style.display = 'block';
                
                // 启用Replay按钮
                const replayBtnEl = document.getElementById('replay-btn');
                replayBtnEl.disabled = false;
                
                // 保存当前选中的请求ID
                window.currentRequestId = request.id;
                
                // 隐藏之前的Replay结果
                const replayResultEl = document.getElementById('replay-result');
                replayResultEl.style.display = 'none';
            }
            
            // 使用 fetch API 获取数据
            async function fetchRequests() {
                try {
                    const response = await fetch('http://127.0.0.1:5000/api/requests');
                    
                    if (!response.ok) {
                        throw new Error(`HTTP 错误: ${response.status}`);
                    }
                    
                    const requests = await response.json();
                    showRequestList(requests);
                    
                } catch (error) {
                    console.error('获取数据失败:', error);
                    showError(`获取数据失败: ${error.message}`);
                }
            }

            const buildTraceSocketUrl = () => {
                const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
                return `${protocol}://${window.location.host}/ws/traces`;
            };

            const handleTraceMessage = (rawData) => {
                try {
                    const trace = JSON.parse(rawData);
                    allRequests = [trace, ...allRequests.filter(r => r.id !== trace.id)];
                    applyFilter();
                } catch (error) {
                    console.warn('无法解析实时 trace:', error);
                }
            };

            const connectTraceSocket = () => {
                // Keep the trace list fresh via a lightweight WebSocket stream
                if (!window.WebSocket) {
                    console.warn('WebSocket 未被支持，实时更新将不可用');
                    return;
                }

                if (traceSocket && traceSocket.readyState === WebSocket.OPEN) {
                    return;
                }

                traceSocket = new WebSocket(buildTraceSocketUrl());
                traceSocket.addEventListener('open', () => {
                    if (traceReconnectTimer) {
                        clearTimeout(traceReconnectTimer);
                        traceReconnectTimer = null;
                    }
                });

                traceSocket.addEventListener('message', (event) => {
                    handleTraceMessage(event.data);
                });

                traceSocket.addEventListener('close', () => {
                    traceReconnectTimer = setTimeout(connectTraceSocket, 2000);
                });

                traceSocket.addEventListener('error', () => {
                    traceSocket.close();
                });
            };
            
            // Replay 请求
            async function replayRequest(requestId) {
                const replayBtnEl = document.getElementById('replay-btn');
                const replayLoadingEl = document.getElementById('replay-loading');
                const replayErrorEl = document.getElementById('replay-error');
                const replayContentEl = document.getElementById('replay-content');
                const replayResultEl = document.getElementById('replay-result');
                
                // 显示结果区域
                replayResultEl.style.display = 'block';
                
                // 显示Loading，隐藏其他
                replayLoadingEl.style.display = 'block';
                replayErrorEl.style.display = 'none';
                replayContentEl.style.display = 'none';
                
                // 添加按钮Loading动画
                replayBtnEl.classList.add('loading');
                replayBtnEl.disabled = true;
                
                try {
                    // 添加1秒延迟以确保Loading动画可见
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    
                    const response = await fetch(`http://127.0.0.1:5000/api/replay/${requestId}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    // 隐藏Loading
                    replayLoadingEl.style.display = 'none';
                    
                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.error || `HTTP 错误: ${response.status}`);
                    }
                    
                    const result = await response.json();
                    
                    // 显示结果
                    const resultHtml = `
                        <div class="replay-item">
                            <span class="replay-label">状态码</span>
                            <div class="replay-value">${result.status_code}</div>
                        </div>
                        <div class="replay-item">
                            <span class="replay-label">响应体</span>
                            <div class="replay-value">${result.response_body || '(空)'}</div>
                        </div>
                    `;
                    
                    replayContentEl.innerHTML = resultHtml;
                    replayContentEl.style.display = 'block';
                    
                } catch (error) {
                    console.error('Replay 失败:', error);
                    
                    // 隐藏Loading，显示错误
                    replayLoadingEl.style.display = 'none';
                    replayErrorEl.textContent = `Replay 失败: ${error.message}`;
                    replayErrorEl.style.display = 'block';
                } finally {
                    // 移除按钮Loading动画并恢复按钮状态
                    replayBtnEl.classList.remove('loading');
                    replayBtnEl.disabled = false;
                }
            }
            
            // 页面加载时立即获取数据
            fetchRequests();
            connectTraceSocket();
            
            // 处理筛选输入变化
            function handleFilterChange() {
                // 当用户使用其他筛选器时，清除tag筛选
                window.currentTagFilter = null;
                
                // 移除所有tag的active状态
                const tagElements = document.querySelectorAll('.tag');
                tagElements.forEach(tag => tag.classList.remove('active'));
                
                // 应用筛选
                applyFilter();
            }
            
            // 为筛选输入框添加事件监听
            methodFilterEl.addEventListener('change', handleFilterChange);
            statusFilterEl.addEventListener('change', handleFilterChange);
            urlFilterEl.addEventListener('input', handleFilterChange);
            if (searchInputEl) {
                searchInputEl.addEventListener('input', handleFilterChange);
            }
            
            // 为Replay按钮添加点击事件
            document.getElementById('replay-btn').addEventListener('click', function() {
                if (window.currentRequestId && !this.disabled) {
                    replayRequest(window.currentRequestId);
                }
            });
            
            // 导出CSV功能
            function exportToCSV(requests) {
                if (!requests || requests.length === 0) {
                    alert('没有数据可导出');
                    return;
                }
                
                // 定义CSV列
                const headers = ['ID', 'Method', 'URL', 'Status Code', 'Request Body', 'Response Body', 'Created At'];
                
                // 创建CSV内容
                let csvContent = headers.join(',') + '\n';
                
                requests.forEach(request => {
                    const row = [
                        request.id,
                        `"${request.method}"`,
                        `"${request.url}"`,
                        request.status_code,
                        `"${(request.request_body || '').replace(/"/g, '""')}"`,
                        `"${(request.response_body || '').replace(/"/g, '""')}"`,
                        `"${request.created_at}"`
                    ];
                    csvContent += row.join(',') + '\n';
                });
                
                // 创建下载链接
                const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `flowtrace_requests_${new Date().toISOString().slice(0, 10)}.csv`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
            }
            
            // 导出JSON功能
            function exportToJSON(requests) {
                if (!requests || requests.length === 0) {
                    alert('没有数据可导出');
                    return;
                }
                
                // 创建JSON内容
                const jsonContent = JSON.stringify(requests, null, 2);
                
                // 创建下载链接
                const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `flowtrace_requests_${new Date().toISOString().slice(0, 10)}.json`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
            }
            
            // 为导出按钮添加点击事件
            document.getElementById('export-csv-btn').addEventListener('click', function() {
                const filteredRequests = filterRequests(allRequests);
                exportToCSV(filteredRequests);
            });
            
            document.getElementById('export-json-btn').addEventListener('click', function() {
                const filteredRequests = filterRequests(allRequests);
                exportToJSON(filteredRequests);
            });
        });
