from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

# 从config_api_keys读取API密钥，动态生成config_list
import json
with open('config_api_keys', 'r') as f:
    keys = json.load(f)
    
config_list = [
    {
        "model": "deepseek-chat",
        "api_key": keys.get("openai_api_key", "your-openai-api-key-here"),
        "base_url": "https://api.deepseek.com/v1"
    }
]
llm_config = {
    'config_list': config_list,
    'timeout': 120,
    'temperature': 0
}

app = FastAPI()

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "FinRobot API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Backend is working"}

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
        print(f"收到请求数据: {request}")
        print(f"资产数量: {len(request.assets)}")
        print(f"客户信息: {request.client_profile}")
        
        # 检查API密钥配置
        try:
            register_keys_from_json('config_api_keys')
            
            # 从config_api_keys读取API密钥
            with open('config_api_keys', 'r') as f:
                keys = json.load(f)
                
            config_list = [
                {
                    "model": "deepseek-chat",
                    "api_key": keys.get("openai_api_key", "your-openai-api-key-here"),
                    "base_url": "https://api.deepseek.com/v1"
                }
            ]
            print(f"API配置加载成功，模型数量: {len(config_list)}")
        except Exception as e:
            print(f"API配置加载失败: {e}")
            return {
                "error": "API配置错误",
                "detail": str(e),
                "factor_results": {},
                "cio_result": "由于API配置问题，无法进行分析。请检查API密钥配置。"
            }
        
        # 1. 资产明细转DataFrame
        df = pd.DataFrame([a.dict() for a in request.assets])
        asset_str = df.to_string(index=False)

        # 2. 多因子分析
        factor_prompts = {
            'Value_Factor_Analyst': '你是一名专业的价值因子研究员。请基于输入的资产明细和市场数据，分析每个资产的估值水平（如PE、PB、股息率、市销率等），结合历史分位、行业对比、盈利能力、分红政策等，指出当前哪些资产被低估或高估。输出结构需包含：专业分析、通俗解释、可操作建议、风险提示。请控制在200字以内。',
            #'Growth_Factor_Analyst': '你是一名成长因子研究员。请分析每个资产的营收、净利润、现金流等增长指标，结合行业增速、未来预期、研发投入、市场空间等，判断哪些资产具备高成长潜力。输出结构需包含：专业分析、通俗解释、可操作建议、风险提示。请控制在200字以内。',
            #'Momentum_Factor_Analyst': '你是一名动量因子研究员。请分析每个资产的价格趋势、换手率、资金流向、历史涨跌幅等，结合市场热点、资金面、技术形态，识别强势资产和弱势资产。输出结构需包含：专业分析、通俗解释、可操作建议、风险提示。请控制在200字以内。',
            #'Quality_Factor_Analyst': '你是一名质量因子研究员。请分析每个资产的ROE、ROA、负债率、盈利质量、现金流稳定性等，结合行业对比、历史表现，筛选出财务健康、盈利能力强的资产。输出结构需包含：专业分析、通俗解释、可操作建议、风险提示。请控制在200字以内。',
            #'Volatility_Factor_Analyst': '你是一名波动率因子研究员。请分析每个资产的历史波动率、最大回撤、夏普比率、相关性等，结合市场环境、资产类别，评估风险水平。输出结构需包含：专业分析、通俗解释、可操作建议、风险提示。请控制在200字以内。',
            #'Liquidity_Factor_Analyst': '你是一名流动性因子研究员。请分析每个资产的成交量、买卖价差、赎回周期、流动性风险等，结合市场环境和客户资金需求，评估流动性水平。输出结构需包含：专业分析、通俗解释、可操作建议、风险提示。请控制在200字以内。',
            #'Sentiment_Factor_Analyst': '你是一名情绪因子研究员。请分析新闻、社交媒体、市场情绪指标、资金流向等，判断市场整体情绪和热点板块。输出结构需包含：专业分析、通俗解释、可操作建议、风险提示。请控制在200字以内。',
            #'Macro_Factor_Analyst': '你是一名宏观因子研究员。请分析利率、汇率、通胀、GDP、政策环境等宏观经济指标，结合资产类别、币种、市场，评估对各类资产的影响。输出结构需包含：专业分析、通俗解释、可操作建议、风险提示。请控制在200字以内。'
        }
        
        # 检查是否使用默认API密钥
        if config_list[0].get('api_key') == 'your-openai-api-key-here':
            print("使用默认API密钥，返回模拟分析结果")
            factor_results = {
                'Value_Factor_Analyst': '【价值因子分析】\n专业分析：茅台估值合理，腾讯存在低估，苹果估值偏高。\n通俗解释：茅台价格合理，腾讯具有投资价值，苹果需谨慎。\n可操作建议：增持腾讯，持有茅台，观望苹果。\n风险提示：市场波动影响估值判断。',
                #'Growth_Factor_Analyst': '【成长因子分析】\n专业分析：腾讯在游戏社交领域有增长潜力，苹果面临创新挑战，茅台增长稳定。\n通俗解释：腾讯业务有发展空间，苹果需新产品推动，茅台增长可预期。\n可操作建议：关注腾讯成长机会，对苹果保持谨慎。\n风险提示：政策变化影响科技股增长。',
                #'Momentum_Factor_Analyst': '【动量因子分析】\n专业分析：市场处于调整期，科技股较弱，消费股稳定。\n通俗解释：市场波动大，科技股回调，消费股抗跌。\n可操作建议：关注企稳信号，配置防御性资产。\n风险提示：市场情绪可能继续波动。',
                #'Quality_Factor_Analyst': '【质量因子分析】\n专业分析：茅台ROE和现金流优秀，腾讯盈利强劲，苹果财务健康。\n通俗解释：三家公司都是行业优质企业，财务状况良好。\n可操作建议：长期持有这些优质资产。\n风险提示：行业竞争影响盈利能力。',
                #'Volatility_Factor_Analyst': '【波动率因子分析】\n专业分析：科技股波动率高，消费股稳定，债券波动最小。\n通俗解释：股票风险大，债券相对安全。\n可操作建议：根据风险承受能力调整配置。\n风险提示：市场波动可能超出预期。',
                #'Liquidity_Factor_Analyst': '【流动性因子分析】\n专业分析：A股港股流动性良好，美股最佳，ETF流动性好。\n通俗解释：这些资产都可正常买卖，无流动性问题。\n可操作建议：可正常进行交易操作。\n风险提示：极端市场可能流动性紧张。',
                #'Sentiment_Factor_Analyst': '【情绪因子分析】\n专业分析：市场情绪偏谨慎，投资者对经济前景担忧。\n通俗解释：市场参与者谨慎，不敢大举投资。\n可操作建议：可适当逆向投资，控制仓位。\n风险提示：情绪可能进一步恶化。',
                #'Macro_Factor_Analyst': '【宏观因子分析】\n专业分析：全球经济面临通胀和增长放缓挑战，货币政策不确定。\n通俗解释：经济环境复杂，投资需谨慎。\n可操作建议：关注政策变化，配置防御性资产。\n风险提示：宏观环境变化影响所有资产。'
            }
        else:
            factor_results = {}
            for name, prompt in factor_prompts.items():
                try:
                    agent = SingleAssistant(
                        agent_config={'name': name, 'profile': prompt},
                        llm_config=llm_config
                    )
                    agent.chat(
                        message=f'请对以下资产明细做因子分析，输出结构化建议：\n{asset_str}',
                        use_cache=False
                    )
                    factor_results[name] = agent.assistant.last_message()["content"]
                except Exception as e:
                    print(f"因子分析失败 {name}: {e}")
                    factor_results[name] = f"分析失败: {str(e)}"

        # 3. CIO汇总
        if config_list[0].get('api_key') == 'your-openai-api-key-here':
            cio_result = '''【首席投资官（CIO）全局配置建议】

专业分析：基于多因子分析，当前组合配置合理但需优化。建议采用"平衡型"策略，调整配置比例提升效率。

通俗解释：您的组合包含优质资产，但可通过调整比例让投资更稳健高效。

可操作建议：
1. 稳健型（保守投资者）：股票40%（茅台20%，腾讯15%，苹果5%），债券40%，基金20%。预期收益6-8%，最大回撤-10%。

2. 平衡型（中等风险）：股票60%（茅台25%，腾讯25%，苹果10%），债券25%，基金15%。预期收益8-12%，最大回撤-15%。

3. 进取型（激进投资者）：股票80%（茅台30%，腾讯35%，苹果15%），债券10%，基金10%。预期收益12-18%，最大回撤-25%。

后续跟踪：每月检查表现，每季度评估效果，动态调整。

风险提示：股票有市场风险，汇率波动影响海外资产，政策变化影响行业。建议根据个人情况选择配置方案。'''
        else:
            cio_prompt = '''
你是首席投资官（CIO）。请汇总所有分析师的专业结论，结合客户风险偏好、目标收益、流动性需求和约束，输出最终的资产配置建议。请用专业术语、通俗语言和可操作建议三层结构，详细解释配置理由、主要风险点、动态调整建议，并给出后续跟踪和复盘建议。针对客户实际情况，给出多种全局配置方案（如稳健型、平衡型、进取型），并说明每种方案的预期收益、风险概率、适用客户类型。输出结构需包含：专业分析、通俗解释、可操作建议、后续跟踪、风险提示。请控制在500字以内。
'''
            try:
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
            except Exception as e:
                print(f"CIO分析失败: {e}")
                cio_result = f"CIO分析失败: {str(e)}"

        return {
            "factor_results": factor_results,
            "cio_result": cio_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
