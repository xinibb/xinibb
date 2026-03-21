"""
策略决策节点
功能：基于剥头皮策略分析行情并生成交易信号
"""
import os
import json
from jinja2 import Template
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient
from langchain_core.messages import SystemMessage, HumanMessage
from graphs.state import StrategyDecisionInput, StrategyDecisionOutput


def strategy_decision_node(
    state: StrategyDecisionInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> StrategyDecisionOutput:
    """
    策略决策节点（Agent节点）
    
    title: 剥头皮策略决策
    desc: 基于剥头皮策略分析行情数据，生成买入/卖出/持有信号
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    try:
        # 读取配置文件
        cfg_path = os.path.join(
            os.getenv("COZE_WORKSPACE_PATH"),
            config.get("metadata", {}).get("llm_cfg", "config/strategy_decision_cfg.json")
        )
        
        with open(cfg_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        
        llm_config = cfg.get("config", {})
        sp = cfg.get("sp", "")
        up = cfg.get("up", "")
        
        # 渲染用户提示词
        up_template = Template(up)
        user_prompt = up_template.render(
            trading_pair=state.trading_pair,
            current_price=state.current_price,
            available_balance=state.available_balance,
            kline_data=json.dumps(state.kline_data[:10], indent=2, ensure_ascii=False),
            positions=json.dumps(state.positions, indent=2, ensure_ascii=False) if state.positions else "无持仓"
        )
        
        # 初始化LLM客户端
        client = LLMClient(ctx=ctx)
        
        # 构建消息
        messages = [
            SystemMessage(content=sp),
            HumanMessage(content=user_prompt)
        ]
        
        # 调用大模型
        response = client.invoke(
            messages=messages,
            model=llm_config.get("model", "doubao-seed-1-8-251228"),
            temperature=llm_config.get("temperature", 0.3),
            max_completion_tokens=llm_config.get("max_completion_tokens", 2000)
        )
        
        # 解析响应
        response_content = response.content
        if isinstance(response_content, str):
            content_str = response_content.strip()
        elif isinstance(response_content, list):
            # 处理列表格式
            content_str = " ".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in response_content
            )
        else:
            content_str = str(response_content)
        
        # 尝试解析JSON
        try:
            # 移除可能的markdown代码块标记
            if "```json" in content_str:
                content_str = content_str.split("```json")[1].split("```")[0].strip()
            elif "```" in content_str:
                content_str = content_str.split("```")[1].split("```")[0].strip()
            
            decision = json.loads(content_str)
            
            return StrategyDecisionOutput(
                trade_signal=decision.get("trade_signal", "hold"),
                signal_strength=float(decision.get("signal_strength", 0.0)),
                suggested_quantity=float(decision.get("suggested_quantity", 0.0)),
                suggested_price=float(decision.get("suggested_price", 0.0)),
                reason=decision.get("reason", "")
            )
            
        except json.JSONDecodeError:
            # JSON解析失败，返回hold
            return StrategyDecisionOutput(
                trade_signal="hold",
                signal_strength=0.0,
                suggested_quantity=0.0,
                suggested_price=state.current_price,
                reason="策略分析失败，保持观望"
            )
            
    except Exception as e:
        return StrategyDecisionOutput(
            trade_signal="hold",
            signal_strength=0.0,
            suggested_quantity=0.0,
            suggested_price=state.current_price if state.current_price else 0.0,
            reason=f"策略决策异常: {str(e)}"
        )
