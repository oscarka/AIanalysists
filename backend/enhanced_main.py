# 增强版主服务文件
# 集成提示词工程、Manus学习、多API并发等优化方案

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sys
import os
import asyncio
import time
import json
from concurrent.futures import ThreadPoolExecutor
import threading
import hashlib

# 导入优化模块
from prompt_templates import PromptOptimizer, FactorAnalysisPrompt
from manus_learning import ManusLearningSystem, ContinuousLearningAgent, QualityEvaluator

# 假设finrobot源码在backend/finrobot
sys.path.append(os.path.join(os.path.dirname(__file__), "finrobot"))

from finrobot.utils import register_keys_from_json
from finrobot.agents.workflow import SingleAssistant
import autogen
import pandas as pd

# 注册API密钥
register_keys_from_json('config_api_keys')

# 多API配置
def load_multi_api_config():
    """加载多个API配置"""
    try:
        with open('config_api_keys', 'r') as f:
            keys = json.load(f)
        
        # 如果有多个API密钥，创建多个配置
        api_keys = keys.get("openai_api_key", "").split(",")
        config_list = []
        
        for i, api_key in enumerate(api_keys):
            if api_key.strip():
                config_list.append({
                    "model": "deepseek-chat",
                    "api_key": api_key.strip(),
                    "base_url": "https://api.deepseek.com/v1"
                })
        
        # 如果没有多个密钥，使用默认配置
        if not config_list:
            config_list = [{
                "model": "deepseek-chat",
                "api_key": keys.get("openai_api_key", "your-openai-api-key-here"),
                "base_url": "https://api.deepseek.com/v1"
            }]
        
        return config_list
    except Exception as e:
        print(f"加载API配置失败: {e}")
        return [{
            "model": "deepseek-chat",
            "api_key": "your-openai-api-key-here",
            "base_url": "https://api.deepseek.com/v1"
        }]

# 全局配置
config_list = load_multi_api_config()
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

# 全局学习系统
learning_system = ManusLearningSystem()
quality_evaluator = QualityEvaluator()

# 缓存机制
class ResponseCache:
    def __init__(self, max_size=100):
        self.cache = {}
        self.max_size = max_size
        self.lock = threading.Lock()
    
    def get_cache_key(self, assets_str: str, client_profile: Dict) -> str:
        """生成缓存键"""
        content = f"{assets_str}_{json.dumps(client_profile, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, key: str) -> Any:
        """获取缓存"""
        with self.lock:
            return self.cache.get(key)
    
    def set(self, key: str, value: Any):
        """设置缓存"""
        with self.lock:
            if len(self.cache) >= self.max_size:
                first_key = next(iter(self.cache))
                del self.cache[first_key]
            self.cache[key] = value

# 全局缓存实例
response_cache = ResponseCache()

# 性能监控
class PerformanceMonitor:
    def __init__(self):
        self.response_times = []
        self.agent_times = {}
        self.lock = threading.Lock()
    
    def record_time(self, agent_name: str, duration: float):
        with self.lock:
            if agent_name not in self.agent_times:
                self.agent_times[agent_name] = []
            self.agent_times[agent_name].append(duration)
            self.response_times.append(duration)
    
    def get_stats(self):
        with self.lock:
            return {
                "total_requests": len(self.response_times),
                "avg_response_time": sum(self.response_times) / len(self.response_times) if self.response_times else 0,
                "agent_stats": {
                    name: {
                        "count": len(times),
                        "avg_time": sum(times) / len(times) if times else 0,
                        "min_time": min(times) if times else 0,
                        "max_time": max(times) if times else 0
                    }
                    for name, times in self.agent_times.items()
                }
            }

performance_monitor = PerformanceMonitor()

@app.get("/")
def read_root():
    return {"message": "Enhanced FinRobot API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Backend is working"}

@app.get("/performance")
def get_performance_stats():
    """获取性能统计"""
    return performance_monitor.get_stats()

@app.get("/learning-insights")
def get_learning_insights():
    """获取学习洞察"""
    insights = {}
    for agent_name in ['Value_Factor_Analyst', 'Growth_Factor_Analyst', 'Momentum_Factor_Analyst', 'Quality_Factor_Analyst']:
        insights[agent_name] = learning_system.analyze_agent_performance(agent_name)
    return insights

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
    use_cache: bool = True
    enable_learning: bool = True  # 是否启用学习功能

def process_single_agent_enhanced(agent_config: Dict, llm_config: Dict, message: str, 
                                api_index: int = 0, enable_learning: bool = True) -> Dict[str, Any]:
    """增强的单个agent处理函数"""
    start_time = time.time()
    
    try:
        # 使用指定的API配置
        agent_llm_config = llm_config.copy()
        if api_index < len(config_list):
            agent_llm_config['config_list'] = [config_list[api_index]]
        
        # 如果启用学习功能，使用优化的提示词
        if enable_learning:
            # 使用提示词优化器
            optimizer = PromptOptimizer()
            optimized_prompt = optimizer.create_optimized_prompt(
                agent_config['name'].replace('_', ' '),
                message,
                json.dumps(agent_config.get('context', {}))
            )
            agent_config['profile'] = optimized_prompt
        
        agent = SingleAssistant(
            agent_config=agent_config,
            llm_config=agent_llm_config
        )
        
        agent.chat(message=message, use_cache=False)
        result = agent.assistant.last_message()["content"]
        
        duration = time.time() - start_time
        performance_monitor.record_time(agent_config['name'], duration)
        
        # 如果启用学习功能，评估质量并记录
        if enable_learning:
            expected_sections = ['专业分析', '通俗解释', '可操作建议', '风险提示']
            quality_score = quality_evaluator.evaluate_response(result, expected_sections)
            
            # 记录学习样本
            from manus_learning import LearningExample
            example = LearningExample(
                input_data={'message': message, 'agent_config': agent_config},
                expected_output="",  # 这里应该有期望输出
                actual_output=result,
                quality_score=quality_score,
                timestamp=time.time(),
                agent_name=agent_config['name'],
                prompt_version="enhanced_v1"
            )
            learning_system.add_example(example)
        
        return {
            'result': result,
            'duration': duration,
            'quality_score': quality_score if enable_learning else None
        }
        
    except Exception as e:
        duration = time.time() - start_time
        performance_monitor.record_time(agent_config['name'], duration)
        raise e

@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    try:
        print(f"收到请求数据: {request}")
        print(f"资产数量: {len(request.assets)}")
        print(f"客户信息: {request.client_profile}")
        print(f"启用学习功能: {request.enable_learning}")
        
        # 1. 资产明细转DataFrame
        df = pd.DataFrame([a.dict() for a in request.assets])
        asset_str = df.to_string(index=False)
        
        # 2. 检查缓存
        if request.use_cache:
            cache_key = response_cache.get_cache_key(asset_str, request.client_profile)
            cached_result = response_cache.get(cache_key)
            if cached_result:
                print("使用缓存结果")
                return cached_result
        
        # 3. 检查API密钥配置
        if config_list[0].get('api_key') == 'your-openai-api-key-here':
            print("使用默认API密钥，返回模拟分析结果")
            factor_results = {
                'Value_Factor_Analyst': '【价值因子分析】\n专业分析：茅台估值合理，腾讯存在低估，苹果估值偏高。\n通俗解释：茅台价格合理，腾讯具有投资价值，苹果需谨慎。\n可操作建议：增持腾讯，持有茅台，观望苹果。\n风险提示：市场波动影响估值判断。',
            }
            cio_result = '''【首席投资官（CIO）全局配置建议】\n专业分析：基于多因子分析，当前组合配置合理但需优化。建议采用"平衡型"策略，调整配置比例提升效率。\n通俗解释：您的组合包含优质资产，但可通过调整比例让投资更稳健高效。\n可操作建议：\n1. 稳健型（保守投资者）：股票40%（茅台20%，腾讯15%，苹果5%），债券40%，基金20%。预期收益6-8%，最大回撤-10%。\n2. 平衡型（中等风险）：股票60%（茅台25%，腾讯25%，苹果10%），债券25%，基金15%。预期收益8-12%，最大回撤-15%。\n3. 进取型（激进投资者）：股票80%（茅台30%，腾讯35%，苹果15%），债券10%，基金10%。预期收益12-18%，最大回撤-25%。\n后续跟踪：每月检查表现，每季度评估效果，动态调整。\n风险提示：股票有市场风险，汇率波动影响海外资产，政策变化影响行业。建议根据个人情况选择配置方案。'''
        else:
            # 4. 多因子分析 - 并发处理
            factor_prompts = {
                'Value_Factor_Analyst': {
                    'profile': '你是一名专业的价值因子研究员。请基于输入的资产明细和市场数据，分析每个资产的估值水平（如PE、PB、股息率、市销率等），结合历史分位、行业对比、盈利能力、分红政策等，指出当前哪些资产被低估或高估。输出结构需包含：专业分析、通俗解释、可操作建议、风险提示。请控制在200字以内。',
                    'context': {'asset_type': 'equity', 'analysis_focus': 'valuation'}
                },
                'Growth_Factor_Analyst': {
                    'profile': '你是一名成长因子研究员。请分析每个资产的营收、净利润、现金流等增长指标，结合行业增速、未来预期、研发投入、市场空间等，判断哪些资产具备高成长潜力。输出结构需包含：专业分析、通俗解释、可操作建议、风险提示。请控制在200字以内。',
                    'context': {'asset_type': 'equity', 'analysis_focus': 'growth'}
                },
                'Momentum_Factor_Analyst': {
                    'profile': '你是一名动量因子研究员。请分析每个资产的价格趋势、换手率、资金流向、历史涨跌幅等，结合市场热点、资金面、技术形态，识别强势资产和弱势资产。输出结构需包含：专业分析、通俗解释、可操作建议、风险提示。请控制在200字以内。',
                    'context': {'asset_type': 'equity', 'analysis_focus': 'momentum'}
                },
                'Quality_Factor_Analyst': {
                    'profile': '你是一名质量因子研究员。请分析每个资产的ROE、ROA、负债率、盈利质量、现金流稳定性等，结合行业对比、历史表现，筛选出财务健康、盈利能力强的资产。输出结构需包含：专业分析、通俗解释、可操作建议、风险提示。请控制在200字以内。',
                    'context': {'asset_type': 'equity', 'analysis_focus': 'quality'}
                },
            }
            
            # 使用线程池并发处理
            factor_results = {}
            quality_scores = {}
            
            with ThreadPoolExecutor(max_workers=min(len(config_list), len(factor_prompts))) as executor:
                futures = []
                
                for i, (name, config) in enumerate(factor_prompts.items()):
                    agent_config = {
                        'name': name, 
                        'profile': config['profile'],
                        'context': config['context']
                    }
                    api_index = i % len(config_list)  # 轮询分配API
                    
                    future = executor.submit(
                        process_single_agent_enhanced,
                        agent_config,
                        llm_config,
                        f'请对以下资产明细做因子分析，输出结构化建议：\n{asset_str}',
                        api_index,
                        request.enable_learning
                    )
                    futures.append((name, future))
                
                # 收集结果
                for name, future in futures:
                    try:
                        result_data = future.result(timeout=180)  # 3分钟超时
                        factor_results[name] = result_data['result']
                        if result_data.get('quality_score') is not None:
                            quality_scores[name] = result_data['quality_score']
                    except Exception as e:
                        print(f"因子分析失败 {name}: {e}")
                        factor_results[name] = f"分析失败: {str(e)}"
            
            # 5. CIO汇总
            cio_prompt = '''你是首席投资官（CIO）。请汇总所有分析师的专业结论，结合客户风险偏好、目标收益、流动性需求和约束，输出最终的资产配置建议。请用专业术语、通俗语言和可操作建议三层结构，详细解释配置理由、主要风险点、动态调整建议，并给出后续跟踪和复盘建议。针对客户实际情况，给出多种全局配置方案（如稳健型、平衡型、进取型），并说明每种方案的预期收益、风险概率、适用客户类型。输出结构需包含：专业分析、通俗解释、可操作建议、后续跟踪、风险提示。请控制在500字以内。'''
            
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
        
        # 6. 缓存结果
        result = {
            "factor_results": factor_results,
            "cio_result": cio_result,
            "quality_scores": quality_scores if request.enable_learning else None,
            "learning_enabled": request.enable_learning
        }
        
        if request.use_cache:
            cache_key = response_cache.get_cache_key(asset_str, request.client_profile)
            response_cache.set(cache_key, result)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)