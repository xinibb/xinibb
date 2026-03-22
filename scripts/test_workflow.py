#!/usr/bin/env python3
"""
欧易量化交易系统 - 快速测试脚本
用于验证工作流是否正常运行
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graphs.graph import main_graph


def test_workflow():
    """测试工作流基本功能"""
    print("=" * 60)
    print("欧易量化交易系统 - 功能测试")
    print("=" * 60)
    
    # 测试参数
    test_input = {
        "trading_pair": "BTC-USDT",
        "initial_capital": 10000.0,
        "strategy_type": "scalping",
        "risk_config": {
            "max_position_ratio": 0.3,      # 最大仓位30%
            "stop_loss_percent": 0.02,       # 止损2%
            "take_profit_percent": 0.05,     # 止盈5%
            "max_daily_loss": 0.1            # 最大日亏损10%
        },
        "notification_config": {
            "enable_email": False,           # 测试时关闭邮件通知
            "enable_wechat": False,
            "enable_feishu": False
        }
    }
    
    print("\n📊 测试参数:")
    print(f"  交易对: {test_input['trading_pair']}")
    print(f"  初始资金: ${test_input['initial_capital']}")
    print(f"  策略类型: {test_input['strategy_type']}")
    print(f"  风控配置: 止损{test_input['risk_config']['stop_loss_percent']*100}% / 止盈{test_input['risk_config']['take_profit_percent']*100}%")
    
    print("\n🚀 开始执行工作流...")
    print("-" * 60)
    
    try:
        # 执行工作流
        result = main_graph.invoke(test_input)
        
        print("\n✅ 工作流执行成功！")
        print("-" * 60)
        print("\n📈 执行结果:")
        print(f"  状态: {result.status}")
        print(f"  消息: {result.message}")
        print(f"  总收益: ${result.total_profit:.2f}")
        print(f"  收益率: {result.profit_rate:.2f}%")
        print(f"  风险等级: {result.risk_level}")
        print(f"  最后交易时间: {result.last_trade_time}")
        
        print("\n" + "=" * 60)
        print("✅ 测试完成！系统运行正常")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def check_dependencies():
    """检查依赖是否安装"""
    print("\n🔍 检查依赖包...")
    
    required_packages = {
        'cozeloop': 'cozeloop',
        'coze_coding_utils': 'coze-coding-utils',
        'coze_coding_dev_sdk': 'coze-coding-dev-sdk',
        'langgraph': 'langgraph',
        'langchain': 'langchain',
        'fastapi': 'fastapi',
        'requests': 'requests'
    }
    
    missing = []
    for module, package in required_packages.items():
        try:
            __import__(module)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - 未安装")
            missing.append(package)
    
    if missing:
        print(f"\n❌ 缺少依赖包: {', '.join(missing)}")
        print("\n请运行以下命令安装:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    print("\n✅ 所有依赖已安装")
    return True


if __name__ == "__main__":
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 运行测试
    success = test_workflow()
    sys.exit(0 if success else 1)
