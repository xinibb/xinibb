"""
FastAPI主应用

提供RESTful API接口
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import json

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.base import (
    Order, OrderCreate, OrderQuery,
    Position, Account, Balance,
    Ticker, Kline, Depth,
    RiskStatus, RiskConfig,
    Trade, TradeMode, SystemConfig,
    ApiResponse, ErrorResponse
)
from backend.core.trading.simulated import SimulatedTrader
from backend.core.trading.okx import OKXTrader
from backend.core.trading.base import BaseTrader
from backend.core.market.client import MarketClient
from backend.core.risk.manager import RiskManager
from backend.core.notification.manager import NotificationManager


# ==================== 配置 ====================

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载配置
CONFIG_FILE = Path(__file__).parent.parent.parent / "config" / "settings.json"

def load_config() -> dict:
    """加载配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "trade_mode": "simulated",
        "initial_capital": 10000.0,
        "default_symbol": "BTC-USDT",
        "enable_notification": False
    }

def save_config(config: dict):
    """保存配置"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

# 初始化配置
config = load_config()

# ==================== 创建应用 ====================

app = FastAPI(
    title="欧易量化交易系统",
    description="前后端分离的量化交易平台",
    version="2.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")

# ==================== 全局实例 ====================

# 交易器
trader: Optional[BaseTrader] = None

# 行情客户端
market_client: Optional[MarketClient] = None

# 风控管理器
risk_manager: Optional[RiskManager] = None

# 通知管理器
notification_manager: Optional[NotificationManager] = None

# ==================== 启动和关闭事件 ====================

@app.on_event("startup")
async def startup_event():
    """启动事件"""
    global trader, market_client, risk_manager, notification_manager
    
    logger.info("正在启动系统...")
    
    # 初始化交易器
    if config["trade_mode"] == "simulated":
        trader = SimulatedTrader(initial_capital=config.get("initial_capital", 10000.0))
    else:
        # 真实交易需要API密钥
        api_key = os.getenv("OKX_API_KEY")
        secret_key = os.getenv("OKX_SECRET_KEY")
        passphrase = os.getenv("OKX_PASSPHRASE")
        
        if not all([api_key, secret_key, passphrase]):
            logger.warning("缺少OKX API配置，使用模拟交易")
            trader = SimulatedTrader(initial_capital=config.get("initial_capital", 10000.0))
        else:
            trader = OKXTrader(api_key, secret_key, passphrase, simulated=True)
    
    # 初始化其他模块
    market_client = MarketClient()
    risk_manager = RiskManager()
    notification_manager = NotificationManager()
    
    logger.info(f"系统启动成功，交易模式: {config['trade_mode']}")

@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    global market_client, notification_manager
    
    logger.info("正在关闭系统...")
    
    if market_client:
        await market_client.close()
    
    if notification_manager:
        await notification_manager.close()
    
    logger.info("系统已关闭")

# ==================== 页面路由 ====================

@app.get("/", response_class=HTMLResponse)
async def index():
    """主页"""
    index_file = FRONTEND_DIR / "pages" / "dashboard.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding='utf-8'))
    return HTMLResponse(content="<h1>欧易量化交易系统</h1><p>前端页面开发中...</p>")

# ==================== 行情API ====================

@app.get("/api/market/ticker/{symbol}", response_model=ApiResponse)
async def get_ticker(symbol: str):
    """获取行情数据"""
    try:
        ticker = await market_client.get_ticker(symbol)
        return ApiResponse(success=True, data=ticker.dict())
    except Exception as e:
        logger.error(f"获取行情失败: {e}")
        return ApiResponse(success=False, message=str(e))

@app.get("/api/market/kline/{symbol}", response_model=ApiResponse)
async def get_kline(
    symbol: str,
    interval: str = Query("1m", description="K线周期"),
    limit: int = Query(100, le=500, description="返回数量")
):
    """获取K线数据"""
    try:
        klines = await market_client.get_kline(symbol, interval, limit)
        return ApiResponse(
            success=True,
            data=[k.dict() for k in klines]
        )
    except Exception as e:
        logger.error(f"获取K线失败: {e}")
        return ApiResponse(success=False, message=str(e))

@app.get("/api/market/depth/{symbol}", response_model=ApiResponse)
async def get_depth(symbol: str, limit: int = Query(20, le=100)):
    """获取市场深度"""
    try:
        depth = await market_client.get_depth(symbol, limit)
        return ApiResponse(success=True, data=depth.dict())
    except Exception as e:
        logger.error(f"获取深度失败: {e}")
        return ApiResponse(success=False, message=str(e))

# ==================== 交易API ====================

@app.post("/api/trading/order", response_model=ApiResponse)
async def create_order(order: OrderCreate):
    """创建订单"""
    try:
        # 检查订单金额
        if order.price:
            order_value = order.amount * order.price
        else:
            # 市价单需要查询当前价格
            ticker = await market_client.get_ticker(order.symbol)
            order_value = order.amount * ticker.last_price
        
        check_result = risk_manager.check_order_amount(order_value)
        if not check_result["passed"]:
            return ApiResponse(success=False, message=check_result["message"])
        
        # 创建订单
        new_order = await trader.create_order(order)
        
        # 发送通知
        if config.get("enable_notification"):
            await notification_manager.notify_all(
                f"新订单: {new_order.order_id}\n"
                f"交易对: {order.symbol}\n"
                f"方向: {order.side}\n"
                f"数量: {order.amount}\n"
                f"价格: {order.price or '市价'}"
            )
        
        return ApiResponse(success=True, data=new_order.dict(), message="订单创建成功")
    except Exception as e:
        logger.error(f"创建订单失败: {e}")
        return ApiResponse(success=False, message=str(e))

@app.delete("/api/trading/order/{order_id}", response_model=ApiResponse)
async def cancel_order(order_id: str, symbol: str = Query(..., description="交易对")):
    """撤销订单"""
    try:
        success = await trader.cancel_order(order_id, symbol)
        return ApiResponse(success=success, message="订单撤销成功" if success else "撤销失败")
    except Exception as e:
        logger.error(f"撤销订单失败: {e}")
        return ApiResponse(success=False, message=str(e))

@app.get("/api/trading/orders", response_model=ApiResponse)
async def get_orders(
    symbol: Optional[str] = Query(None, description="交易对"),
    status: Optional[str] = Query(None, description="订单状态"),
    limit: int = Query(100, le=500)
):
    """查询订单列表"""
    try:
        from backend.models.base import OrderStatus
        status_enum = OrderStatus(status) if status else None
        
        orders = await trader.get_orders(symbol, status_enum, limit)
        return ApiResponse(
            success=True,
            data=[o.dict() for o in orders]
        )
    except Exception as e:
        logger.error(f"查询订单失败: {e}")
        return ApiResponse(success=False, message=str(e))

@app.get("/api/trading/order/{order_id}", response_model=ApiResponse)
async def get_order(order_id: str, symbol: str = Query(..., description="交易对")):
    """查询订单详情"""
    try:
        order = await trader.get_order(order_id, symbol)
        if order:
            return ApiResponse(success=True, data=order.dict())
        return ApiResponse(success=False, message="订单不存在")
    except Exception as e:
        logger.error(f"查询订单失败: {e}")
        return ApiResponse(success=False, message=str(e))

# ==================== 账户API ====================

@app.get("/api/account/balance", response_model=ApiResponse)
async def get_balance(currency: str = Query("USDT", description="币种")):
    """查询余额"""
    try:
        balance = await trader.get_balance(currency)
        return ApiResponse(success=True, data=balance.dict())
    except Exception as e:
        logger.error(f"查询余额失败: {e}")
        return ApiResponse(success=False, message=str(e))

@app.get("/api/account/info", response_model=ApiResponse)
async def get_account():
    """查询账户信息"""
    try:
        account = await trader.get_account()
        return ApiResponse(success=True, data=account.dict())
    except Exception as e:
        logger.error(f"查询账户失败: {e}")
        return ApiResponse(success=False, message=str(e))

@app.get("/api/account/positions", response_model=ApiResponse)
async def get_positions(symbol: Optional[str] = Query(None, description="交易对")):
    """查询持仓"""
    try:
        positions = await trader.get_positions(symbol)
        return ApiResponse(
            success=True,
            data=[p.dict() for p in positions]
        )
    except Exception as e:
        logger.error(f"查询持仓失败: {e}")
        return ApiResponse(success=False, message=str(e))

# ==================== 风控API ====================

@app.get("/api/risk/status", response_model=ApiResponse)
async def get_risk_status():
    """查询风控状态"""
    try:
        account = await trader.get_account()
        positions = await trader.get_positions()
        
        # 更新持仓当前价格
        for pos in positions:
            ticker = await market_client.get_ticker(pos.symbol)
            pos.current_price = ticker.last_price
        
        status = risk_manager.evaluate_risk_level(account, positions)
        return ApiResponse(success=True, data=status.dict())
    except Exception as e:
        logger.error(f"查询风控状态失败: {e}")
        return ApiResponse(success=False, message=str(e))

# ==================== 系统API ====================

@app.get("/api/system/status", response_model=ApiResponse)
async def get_system_status():
    """查询系统状态"""
    try:
        health = await trader.health_check()
        return ApiResponse(
            success=True,
            data={
                "status": "running",
                "trade_mode": config["trade_mode"],
                "health": health,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"查询系统状态失败: {e}")
        return ApiResponse(success=False, message=str(e))

@app.get("/api/system/config", response_model=ApiResponse)
async def get_config():
    """查询系统配置"""
    return ApiResponse(success=True, data=config)

@app.post("/api/system/config", response_model=ApiResponse)
async def update_config(new_config: dict = Body(...)):
    """更新系统配置"""
    global config, trader
    
    try:
        # 更新配置
        config.update(new_config)
        save_config(config)
        
        # 如果交易模式改变，需要重新初始化交易器
        if "trade_mode" in new_config:
            logger.info(f"交易模式切换: {new_config['trade_mode']}")
            # 这里需要重新创建交易器，暂时只更新配置
        
        return ApiResponse(success=True, message="配置更新成功")
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        return ApiResponse(success=False, message=str(e))

# ==================== 主入口 ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )
