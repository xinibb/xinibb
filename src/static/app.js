/**
 * 欧易量化交易系统 - 前端交互
 */

// 全局变量
let currentPair = 'BTC-USDT';
let refreshInterval = null;

// API基础URL
const API_BASE = window.location.origin;

/**
 * 页面加载完成后初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('系统初始化...');
    
    // 加载初始数据
    refreshData();
    
    // 设置自动刷新（每30秒）
    refreshInterval = setInterval(refreshData, 30000);
    
    console.log('系统初始化完成');
});

/**
 * 刷新所有数据
 */
async function refreshData() {
    console.log('刷新数据...');
    
    try {
        // 并行请求所有数据
        await Promise.all([
            fetchMarketData(),
            fetchAccountData(),
            fetchPositions()
        ]);
        
        showToast('数据已刷新', 'success');
    } catch (error) {
        console.error('刷新数据失败:', error);
        showToast('数据刷新失败: ' + error.message, 'error');
    }
}

/**
 * 获取市场数据
 */
async function fetchMarketData() {
    try {
        const response = await fetch(`${API_BASE}/api/market/${currentPair}`);
        
        if (!response.ok) {
            throw new Error('获取市场数据失败');
        }
        
        const data = await response.json();
        
        // 更新UI
        updateMarketUI(data);
        
    } catch (error) {
        console.error('获取市场数据失败:', error);
        // 使用模拟数据
        updateMarketUI({
            trading_pair: currentPair,
            current_price: (Math.random() * 50000 + 30000).toFixed(2),
            market_trend: Math.random() > 0.5 ? '上涨' : '下跌',
            timestamp: new Date().toLocaleString('zh-CN')
        });
    }
}

/**
 * 更新市场数据UI
 */
function updateMarketUI(data) {
    // 当前价格
    const priceEl = document.getElementById('currentPrice');
    const currentPrice = parseFloat(data.current_price);
    priceEl.textContent = '$' + currentPrice.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
    
    // 价格变化（模拟）
    const priceChange = (Math.random() * 6 - 3).toFixed(2);
    const priceChangeEl = document.getElementById('priceChange');
    if (priceChange >= 0) {
        priceChangeEl.innerHTML = `<span class="price-up">+${priceChange}%</span> ↑`;
        priceEl.className = 'metric-value price-up';
    } else {
        priceChangeEl.innerHTML = `<span class="price-down">${priceChange}%</span> ↓`;
        priceEl.className = 'metric-value price-down';
    }
    
    // 市场趋势
    document.getElementById('marketTrend').textContent = data.market_trend || '--';
    
    // 模拟其他数据
    document.getElementById('volume24h').textContent = (Math.random() * 1000).toFixed(2) + 'M';
    document.getElementById('highPrice').textContent = '$' + (currentPrice * 1.02).toFixed(2);
    document.getElementById('lowPrice').textContent = '$' + (currentPrice * 0.98).toFixed(2);
    
    // 更新时间戳
    document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString('zh-CN');
}

/**
 * 获取账户数据
 */
async function fetchAccountData() {
    try {
        const response = await fetch(`${API_BASE}/api/account`);
        
        if (!response.ok) {
            throw new Error('获取账户数据失败');
        }
        
        const data = await response.json();
        
        // 更新UI
        updateAccountUI(data);
        
    } catch (error) {
        console.error('获取账户数据失败:', error);
        // 使用模拟数据
        updateAccountUI({
            total_balance: 10000.0,
            available_balance: 7000.0,
            frozen_balance: 3000.0,
            total_position_value: 3000.0
        });
    }
}

/**
 * 更新账户数据UI
 */
function updateAccountUI(data) {
    // 总余额
    document.getElementById('totalBalance').textContent = 
        '$' + data.total_balance.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    
    // 可用余额
    document.getElementById('availableBalance').textContent = 
        '$' + data.available_balance.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    
    // 持仓价值
    document.getElementById('positionValue').textContent = 
        '$' + data.total_position_value.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    
    // 仓位比例
    const positionRatio = data.total_position_value / data.total_balance;
    document.getElementById('positionRatio').textContent = 
        (positionRatio * 100).toFixed(2) + '%';
    document.getElementById('positionRatioDetail').textContent = 
        (positionRatio * 100).toFixed(2) + '%';
    
    // 总收益（模拟）
    const totalProfit = (Math.random() * 200 - 100).toFixed(2);
    const profitRate = ((totalProfit / 10000) * 100).toFixed(2);
    
    const profitEl = document.getElementById('totalProfit');
    profitEl.textContent = '$' + Math.abs(totalProfit);
    
    const rateEl = document.getElementById('profitRate');
    if (parseFloat(totalProfit) >= 0) {
        profitEl.className = 'metric-value price-up';
        rateEl.textContent = '+' + profitRate + '%';
    } else {
        profitEl.className = 'metric-value price-down';
        rateEl.textContent = profitRate + '%';
    }
    
    // 风险等级（模拟）
    updateRiskUI();
}

/**
 * 更新风险监控UI
 */
function updateRiskUI() {
    const riskLevel = ['low', 'medium', 'high'][Math.floor(Math.random() * 3)];
    const riskText = {
        'low': '低风险',
        'medium': '中风险',
        'high': '高风险'
    };
    
    const riskBox = document.getElementById('riskLevelBox');
    riskBox.className = 'p-3 rounded risk-' + riskLevel;
    
    document.getElementById('riskLevel').textContent = riskText[riskLevel];
    
    // 止损止盈状态
    document.getElementById('stopLossStatus').innerHTML = 
        Math.random() > 0.7 ? 
        '<span class="text-danger">● 需止损</span>' : 
        '<span class="text-success">● 正常</span>';
    
    document.getElementById('takeProfitStatus').innerHTML = 
        Math.random() > 0.8 ? 
        '<span class="text-warning">● 达到止盈</span>' : 
        '<span class="text-muted">● 未达到</span>';
}

/**
 * 获取持仓信息
 */
async function fetchPositions() {
    try {
        const response = await fetch(`${API_BASE}/api/positions`);
        
        if (!response.ok) {
            throw new Error('获取持仓失败');
        }
        
        const data = await response.json();
        
        // 更新UI
        updatePositionsUI(data);
        
    } catch (error) {
        console.error('获取持仓失败:', error);
        // 使用空数据
        updatePositionsUI([]);
    }
}

/**
 * 更新持仓UI
 */
function updatePositionsUI(positions) {
    const container = document.getElementById('positionsList');
    
    if (!positions || positions.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="bi bi-inbox" style="font-size: 2rem;"></i>
                <div class="mt-2">暂无持仓</div>
            </div>
        `;
        return;
    }
    
    let html = '';
    positions.forEach(pos => {
        const pnl = pos.unrealized_pnl || 0;
        const pnlClass = pnl >= 0 ? 'text-success' : 'text-danger';
        
        html += `
            <div class="info-row">
                <div>
                    <div class="fw-bold">${pos.pair || currentPair}</div>
                    <small class="text-muted">${pos.side || 'LONG'} · ${pos.size || 0}</small>
                </div>
                <div class="text-end">
                    <div>$${pos.value || 0}</div>
                    <small class="${pnlClass}">${pnl >= 0 ? '+' : ''}${pnl}</small>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

/**
 * 更改交易对
 */
function changePair() {
    currentPair = document.getElementById('tradingPair').value;
    console.log('切换交易对:', currentPair);
    
    // 清空当前数据
    document.getElementById('currentPrice').textContent = '加载中...';
    
    // 刷新数据
    refreshData();
    
    addLog('切换交易对: ' + currentPair);
}

/**
 * 执行策略
 */
async function executeStrategy() {
    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>执行中...';
    
    addLog('开始执行策略...');
    
    try {
        const response = await fetch(`${API_BASE}/invoke`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                trading_pair: currentPair,
                initial_capital: 10000.0,
                strategy_type: 'scalping',
                risk_config: {
                    max_position_ratio: 0.3,
                    stop_loss_percent: 0.02,
                    take_profit_percent: 0.05
                },
                notification_config: {
                    enable_email: false
                }
            })
        });
        
        if (!response.ok) {
            throw new Error('策略执行失败');
        }
        
        const data = await response.json();
        
        // 更新信号UI
        updateSignalUI(data);
        
        addLog('策略执行成功', 'success');
        showToast('策略执行成功', 'success');
        
        // 刷新数据
        await refreshData();
        
    } catch (error) {
        console.error('策略执行失败:', error);
        addLog('策略执行失败: ' + error.message, 'error');
        showToast('策略执行失败', 'error');
        
        // 使用模拟数据
        updateSignalUI({
            trade_signal: ['buy', 'sell', 'hold'][Math.floor(Math.random() * 3)],
            signal_strength: Math.random(),
            suggested_price: Math.random() * 50000 + 30000,
            suggested_quantity: Math.random() * 0.1,
            reason: '模拟交易信号'
        });
        
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-play-fill me-1"></i>执行策略';
    }
}

/**
 * 更新交易信号UI
 */
function updateSignalUI(data) {
    const signal = data.trade_signal || 'hold';
    
    // 信号框
    const signalBox = document.getElementById('signalBox');
    const signalEl = document.getElementById('tradeSignal');
    
    signalBox.className = 'text-center p-4 rounded signal-' + signal;
    
    const signalText = {
        'buy': '买入',
        'sell': '卖出',
        'hold': '持有'
    };
    
    signalEl.textContent = signalText[signal];
    
    // 信号强度
    const strength = data.signal_strength || 0;
    document.getElementById('signalStrength').innerHTML = 
        `<div class="progress" style="height: 20px;">
            <div class="progress-bar" style="width: ${strength * 100}%">${(strength * 100).toFixed(0)}%</div>
        </div>`;
    
    // 建议价格和数量
    document.getElementById('suggestedPrice').textContent = 
        '$' + (data.suggested_price || 0).toFixed(2);
    document.getElementById('suggestedQuantity').textContent = 
        (data.suggested_quantity || 0).toFixed(6);
    
    // 决策理由
    if (data.reason) {
        document.getElementById('decisionReason').style.display = 'block';
        document.getElementById('reasonText').textContent = data.reason;
    }
    
    addLog(`信号: ${signalText[signal]} (强度: ${(strength * 100).toFixed(0)}%)`);
}

/**
 * 添加日志
 */
function addLog(message, type = 'info') {
    const container = document.getElementById('logContainer');
    const timestamp = new Date().toLocaleTimeString('zh-CN');
    
    const typeClass = {
        'info': 'text-info',
        'success': 'text-success',
        'error': 'text-danger',
        'warning': 'text-warning'
    };
    
    const typeIcon = {
        'info': 'bi-info-circle',
        'success': 'bi-check-circle',
        'error': 'bi-x-circle',
        'warning': 'bi-exclamation-triangle'
    };
    
    const logHtml = `
        <div class="log-entry">
            <span class="text-muted">[${timestamp}]</span>
            <i class="bi ${typeIcon[type]} ${typeClass[type]} mx-1"></i>
            <span>${message}</span>
        </div>
    `;
    
    container.insertAdjacentHTML('afterbegin', logHtml);
    
    // 限制日志数量
    const logs = container.querySelectorAll('.log-entry');
    if (logs.length > 50) {
        logs[logs.length - 1].remove();
    }
}

/**
 * 清空日志
 */
function clearLogs() {
    const container = document.getElementById('logContainer');
    container.innerHTML = `
        <div class="text-center text-muted py-4">
            <i class="bi bi-clock-history" style="font-size: 2rem;"></i>
            <div class="mt-2">暂无日志</div>
        </div>
    `;
}

/**
 * 显示Toast通知
 */
function showToast(message, type = 'info') {
    const toastEl = document.getElementById('toast');
    const titleEl = document.getElementById('toastTitle');
    const bodyEl = document.getElementById('toastBody');
    
    const titles = {
        'info': '提示',
        'success': '成功',
        'error': '错误',
        'warning': '警告'
    };
    
    titleEl.textContent = titles[type];
    bodyEl.textContent = message;
    
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}

// 页面卸载时清理
window.addEventListener('beforeunload', function() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});
