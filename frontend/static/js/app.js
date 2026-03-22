/**
 * 欧易量化交易系统 - JavaScript核心库
 */

// API基础URL
const API_BASE = '';

// 工具函数
class Utils {
    /**
     * 格式化数字
     */
    static formatNumber(num, decimals = 2) {
        if (typeof num !== 'number') return '-';
        return num.toFixed(decimals);
    }

    /**
     * 格式化货币
     */
    static formatCurrency(num, currency = '$') {
        if (typeof num !== 'number') return '-';
        return currency + num.toFixed(2);
    }

    /**
     * 格式化百分比
     */
    static formatPercent(num) {
        if (typeof num !== 'number') return '-';
        return (num * 100).toFixed(2) + '%';
    }

    /**
     * 格式化时间
     */
    static formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString('zh-CN');
    }

    /**
     * 显示提示消息
     */
    static showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// API请求封装
class API {
    /**
     * GET请求
     */
    static async get(url, params = {}) {
        const queryStr = Object.keys(params)
            .map(k => `${encodeURIComponent(k)}=${encodeURIComponent(params[k])}`)
            .join('&');
        
        const fullUrl = queryStr ? `${API_BASE}${url}?${queryStr}` : `${API_BASE}${url}`;
        
        try {
            const response = await fetch(fullUrl);
            return await response.json();
        } catch (error) {
            console.error('API GET Error:', error);
            return { success: false, message: error.message };
        }
    }

    /**
     * POST请求
     */
    static async post(url, data = {}) {
        try {
            const response = await fetch(`${API_BASE}${url}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            return await response.json();
        } catch (error) {
            console.error('API POST Error:', error);
            return { success: false, message: error.message };
        }
    }

    /**
     * DELETE请求
     */
    static async delete(url) {
        try {
            const response = await fetch(`${API_BASE}${url}`, {
                method: 'DELETE'
            });
            return await response.json();
        } catch (error) {
            console.error('API DELETE Error:', error);
            return { success: false, message: error.message };
        }
    }
}

// 行情服务
class MarketService {
    /**
     * 获取行情
     */
    static async getTicker(symbol) {
        return API.get(`/api/market/ticker/${symbol}`);
    }

    /**
     * 获取K线
     */
    static async getKline(symbol, interval = '1m', limit = 100) {
        return API.get(`/api/market/kline/${symbol}`, { interval, limit });
    }

    /**
     * 获取深度
     */
    static async getDepth(symbol, limit = 20) {
        return API.get(`/api/market/depth/${symbol}`, { limit });
    }
}

// 交易服务
class TradingService {
    /**
     * 创建订单
     */
    static async createOrder(order) {
        return API.post('/api/trading/order', order);
    }

    /**
     * 撤销订单
     */
    static async cancelOrder(orderId, symbol) {
        return API.delete(`/api/trading/order/${orderId}?symbol=${symbol}`);
    }

    /**
     * 查询订单
     */
    static async getOrders(symbol, status, limit = 100) {
        const params = { limit };
        if (symbol) params.symbol = symbol;
        if (status) params.status = status;
        return API.get('/api/trading/orders', params);
    }

    /**
     * 查询订单详情
     */
    static async getOrder(orderId, symbol) {
        return API.get(`/api/trading/order/${orderId}`, { symbol });
    }
}

// 账户服务
class AccountService {
    /**
     * 查询余额
     */
    static async getBalance(currency = 'USDT') {
        return API.get('/api/account/balance', { currency });
    }

    /**
     * 查询账户信息
     */
    static async getAccount() {
        return API.get('/api/account/info');
    }

    /**
     * 查询持仓
     */
    static async getPositions(symbol) {
        const params = {};
        if (symbol) params.symbol = symbol;
        return API.get('/api/account/positions', params);
    }
}

// 风控服务
class RiskService {
    /**
     * 查询风控状态
     */
    static async getStatus() {
        return API.get('/api/risk/status');
    }
}

// 系统服务
class SystemService {
    /**
     * 查询系统状态
     */
    static async getStatus() {
        return API.get('/api/system/status');
    }

    /**
     * 查询配置
     */
    static async getConfig() {
        return API.get('/api/system/config');
    }

    /**
     * 更新配置
     */
    static async updateConfig(config) {
        return API.post('/api/system/config', config);
    }
}

// 导出
window.Utils = Utils;
window.API = API;
window.MarketService = MarketService;
window.TradingService = TradingService;
window.AccountService = AccountService;
window.RiskService = RiskService;
window.SystemService = SystemService;
