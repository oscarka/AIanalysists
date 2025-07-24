from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import sys
import os

# 假设finrobot源码在backend/finrobot
sys.path.append(os.path.join(os.path.dirname(__file__), "finrobot"))

from finrobot.utils import register_keys_from_json
from finrobot.agents.workflow import SingleAssistant
import autogen
import pandas as pd

# 注册API密钥
register_keys_from_json('config_api_keys')
config_list = autogen.config_list_from_json(
    'OAI_CONFIG_LIST',
    filter_dict={'model': ['deepseek-chat']},
)
llm_config = {
    'config_list': config_list,
    'timeout': 120,
    'temperature': 0
}

app = FastAPI()

class AssetItem(BaseModel):
    name: str
    type: str
    value: float
    cost: float
    price: float
    holding_period: str
    currency: str
    market: str

class AnalyzeRequest(BaseModel):
    assets: List[AssetItem]
    client_profile: Dict[str, Any] = {}

@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    try:
        # 1. 资产明细转DataFrame
        df = pd.DataFrame([a.dict() for a in request.assets])
        asset_str = df.to_string(index=False)

        # 2. 多因子分析
        factor_prompts = {
            'Value_Factor_Analyst': '你是一名专业的价值因子研究员。请基于输入的资产明细和市场数据，分析每个资产的估值水平（如PE、PB、股息率、市销率等），结合历史分位、行业对比、盈利能力、分红政策等，指出当前哪些资产被低估或高估。输出结构需包含：专业分析、通俗解释、可操作建议、风险提示。',
            'Growth_Factor_Analyst': '你是一名成长因子研究员。请分析每个资产的营收、净利润、现金流等增长指标，结合行业增速、未来预期、研发投入、市场空间等，判断哪些资产具备高成长潜力。输出结构需包含：专业分析、通俗解释、可操作建议、风险提示。',
            'Momentum_Factor_Analyst': '你是一名动量因子研究员。请分析每个资产的价格趋势、换手率、资金流向、历史涨跌幅等，结合市场热点、资金面、技术形态，识别强势资产和弱势资产。输出结构需包含：专业分析、通俗解释、可操作建议、风险提示。',
            'Quality_Factor_Analyst': '你是一名质量因子研究员。请分析每个资产的ROE、ROA、负债率、盈利质量、现金流稳定性等，结合行业对比、历史表现，筛选出财务健康、盈利能力强的资产。输出结构需包含：专业分析、通俗解释、可操作建议、风险提示。',
            'Volatility_Factor_Analyst': '你是一名波动率因子研究员。请分析每个资产的历史波动率、最大回撤、夏普比率、相关性等，结合市场环境、资产类别，评估风险水平。输出结构需包含：专业分析、通俗解释、可操作建议、风险提示。',
            'Liquidity_Factor_Analyst': '你是一名流动性因子研究员。请分析每个资产的成交量、买卖价差、赎回周期、流动性风险等，结合市场环境和客户资金需求，评估流动性水平。输出结构需包含：专业分析、通俗解释、可操作建议、风险提示。',
            'Sentiment_Factor_Analyst': '你是一名情绪因子研究员。请分析新闻、社交媒体、市场情绪指标、资金流向等，判断市场整体情绪和热点板块。输出结构需包含：专业分析、通俗解释、可操作建议、风险提示。',
            'Macro_Factor_Analyst': '你是一名宏观因子研究员。请分析利率、汇率、通胀、GDP、政策环境等宏观经济指标，结合资产类别、币种、市场，评估对各类资产的影响。输出结构需包含：专业分析、通俗解释、可操作建议、风险提示。'
        }
        factor_results = {}
        for name, prompt in factor_prompts.items():
            agent = SingleAssistant(
                agent_config={'name': name, 'profile': prompt},
                llm_config=llm_config
            )
            agent.chat(
                message=f'请对以下资产明细做因子分析，输出结构化建议：\n{asset_str}',
                use_cache=False
            )
            factor_results[name] = agent.assistant.last_message()["content"]

        # 3. CIO汇总
        cio_prompt = '''
你是首席投资官（CIO）。请汇总所有分析师的专业结论，结合客户风险偏好、目标收益、流动性需求和约束，输出最终的资产配置建议。请用专业术语、通俗语言和可操作建议三层结构，详细解释配置理由、主要风险点、动态调整建议，并给出后续跟踪和复盘建议。针对客户实际情况，给出多种全局配置方案（如稳健型、平衡型、进取型），并说明每种方案的预期收益、风险概率、适用客户类型。输出结构需包含：专业分析、通俗解释、可操作建议、后续跟踪、风险提示。
'''
        cio_agent = SingleAssistant(
            agent_config={'name': 'CIO', 'profile': cio_prompt},
            llm_config=llm_config
        )
        summary = '\n'.join([f'{k}: {v}' for k, v in factor_results.items()])
        cio_agent.chat(
            message=f'请基于以下多因子分析师结论，输出全局资产配置建议：\n{summary}',
            use_cache=False
        )
        cio_result = cio_agent.assistant.last_message()["content"]

        return {
            "factor_results": factor_results,
            "cio_result": cio_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))