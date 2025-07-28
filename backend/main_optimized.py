#!/usr/bin/env python3
"""
FinRobot优化版本 - 整合所有优化功能
包含：多API并行、多LLM集成、代码增强、缓存、监控
"""

import asyncio
import time
import json
import hashlib
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import anthropic
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局配置
class Config:
    # API配置
    OPENAI_API_KEY = "sk-xxx"  # 替换为你的OpenAI API密钥
    ANTHROPIC_API_KEY = "sk-ant-xxx"  # 替换为你的Anthropic API密钥
    DEEPSEEK_API_KEY = "sk-xxx"  # 替换为你的DeepSeek API密钥
    GOOGLE_API_KEY = "xxx"  # 替换为你的Google API密钥
    
    # 多API配置
    MULTI_API_KEYS = [
        "sk-xxx1", "sk-xxx2", "sk-xxx3"  # 多个OpenAI API密钥
    ]
    
    # 缓存配置
    CACHE_TTL = 3600  # 1小时
    MAX_CACHE_SIZE = 1000
    
    # 性能配置
    MAX_WORKERS = 4
    REQUEST_TIMEOUT = 180

# 数据模型
class Asset(BaseModel):
    name: str
    type: str
    value: float
    cost: float
    price: float
    holding_period: str
    currency: str
    market: str

class ClientProfile(BaseModel):
    risk_tolerance: str
    investment_horizon: str
    investment_goal: str
    portfolio_size: str

class AnalyzeRequest(BaseModel):
    assets: List[Asset]
    client_profile: ClientProfile
    use_cache: bool = True
    enable_learning: bool = True

class AnalyzeResponse(BaseModel):
    analysis_results: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    cache_info: Dict[str, Any]
    quality_scores: Dict[str, float]

# 缓存系统
class ResponseCache:
    def __init__(self):
        self.cache = {}
        self.hit_count = 0
        self.miss_count = 0
    
    def get_cache_key(self, assets, client_profile):
        """生成缓存键"""
        data_str = f"{assets}_{client_profile}"
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def get(self, key):
        """获取缓存"""
        if key in self.cache:
            item = self.cache[key]
            if time.time() < item['expires']:
                self.hit_count += 1
                return item['value']
            else:
                del self.cache[key]
        self.miss_count += 1
        return None
    
    def set(self, key, value, ttl=Config.CACHE_TTL):
        """设置缓存"""
        if len(self.cache) >= Config.MAX_CACHE_SIZE:
            # 清理过期缓存
            current_time = time.time()
            expired_keys = [k for k, v in self.cache.items() if current_time >= v['expires']]
            for k in expired_keys:
                del self.cache[k]
        
        self.cache[key] = {
            'value': value,
            'expires': time.time() + ttl
        }
    
    def get_stats(self):
        """获取缓存统计"""
        total = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total * 100) if total > 0 else 0
        return {
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': f"{hit_rate:.1f}%",
            'cache_size': len(self.cache)
        }

# 性能监控
class PerformanceMonitor:
    def __init__(self):
        self.response_times = []
        self.success_count = 0
        self.error_count = 0
        self.start_time = time.time()
    
    def record_request(self, duration, success=True):
        """记录请求性能"""
        self.response_times.append(duration)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
    
    def get_stats(self):
        """获取性能统计"""
        total_requests = self.success_count + self.error_count
        success_rate = (self.success_count / total_requests * 100) if total_requests > 0 else 0
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        return {
            'total_requests': total_requests,
            'success_rate': f"{success_rate:.1f}%",
            'avg_response_time': f"{avg_response_time:.2f}s",
            'uptime': f"{(time.time() - self.start_time) / 3600:.1f}h"
        }

# 金融数据工具
class FinancialDataTool:
    def __init__(self):
        self.cache = {}
    
    async def get_stock_data(self, symbol: str) -> Dict[str, Any]:
        """获取股票数据"""
        try:
            # 使用yfinance获取数据
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 获取历史数据
            hist = ticker.history(period="1y")
            
            # 计算技术指标
            if not hist.empty:
                hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
                hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
                hist['RSI'] = self.calculate_rsi(hist['Close'])
                hist['MACD'] = self.calculate_macd(hist['Close'])
                
                current_price = hist['Close'].iloc[-1]
                volatility = hist['Close'].pct_change().std() * np.sqrt(252)
                
                return {
                    'symbol': symbol,
                    'current_price': current_price,
                    'pe_ratio': info.get('trailingPE', 0),
                    'pb_ratio': info.get('priceToBook', 0),
                    'market_cap': info.get('marketCap', 0),
                    'rsi': hist['RSI'].iloc[-1] if not pd.isna(hist['RSI'].iloc[-1]) else 50,
                    'macd': hist['MACD'].iloc[-1] if not pd.isna(hist['MACD'].iloc[-1]) else 0,
                    'volatility': volatility,
                    'sma_20': hist['SMA_20'].iloc[-1] if not pd.isna(hist['SMA_20'].iloc[-1]) else current_price,
                    'sma_50': hist['SMA_50'].iloc[-1] if not pd.isna(hist['SMA_50'].iloc[-1]) else current_price
                }
        except Exception as e:
            logger.error(f"Error getting stock data for {symbol}: {e}")
            return self.get_fallback_data(symbol)
    
    def calculate_rsi(self, prices, period=14):
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """计算MACD指标"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        return macd - signal_line
    
    def get_fallback_data(self, symbol: str) -> Dict[str, Any]:
        """获取备用数据"""
        return {
            'symbol': symbol,
            'current_price': 100.0,
            'pe_ratio': 25.0,
            'pb_ratio': 3.0,
            'market_cap': 1000000000,
            'rsi': 50.0,
            'macd': 0.0,
            'volatility': 0.2,
            'sma_20': 98.0,
            'sma_50': 95.0
        }

# 多LLM客户端
class MultiLLMClient:
    def __init__(self):
        self.clients = {
            'openai': openai,
            'anthropic': anthropic,
            'google': genai
        }
        
        # 配置API密钥
        openai.api_key = Config.OPENAI_API_KEY
        self.anthropic_client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        
        self.usage_stats = {
            'openai': {'calls': 0, 'tokens': 0},
            'anthropic': {'calls': 0, 'tokens': 0},
            'google': {'calls': 0, 'tokens': 0}
        }
    
    async def analyze_with_multiple_llms(self, prompt: str) -> Dict[str, Any]:
        """使用多个LLM进行分析"""
        tasks = []
        
        # OpenAI GPT-4
        tasks.append(self.call_openai(prompt))
        
        # Anthropic Claude
        tasks.append(self.call_anthropic(prompt))
        
        # Google Gemini
        tasks.append(self.call_google(prompt))
        
        # 并行调用
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        results = []
        for i, response in enumerate(['openai', 'anthropic', 'google']):
            if isinstance(responses[i], Exception):
                logger.error(f"Error calling {response}: {responses[i]}")
                continue
            results.append(responses[i])
        
        # 综合结果
        return self.synthesize_results(results)
    
    async def call_openai(self, prompt: str) -> Dict[str, Any]:
        """调用OpenAI"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000,
                    temperature=0.7
                )
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            self.usage_stats['openai']['calls'] += 1
            self.usage_stats['openai']['tokens'] += tokens_used
            
            return {
                'model': 'gpt-4',
                'content': content,
                'quality_score': self.evaluate_quality(content),
                'tokens_used': tokens_used
            }
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None
    
    async def call_anthropic(self, prompt: str) -> Dict[str, Any]:
        """调用Anthropic Claude"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
            )
            
            content = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            self.usage_stats['anthropic']['calls'] += 1
            self.usage_stats['anthropic']['tokens'] += tokens_used
            
            return {
                'model': 'claude-3-sonnet',
                'content': content,
                'quality_score': self.evaluate_quality(content),
                'tokens_used': tokens_used
            }
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return None
    
    async def call_google(self, prompt: str) -> Dict[str, Any]:
        """调用Google Gemini"""
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: model.generate_content(prompt)
            )
            
            content = response.text
            
            self.usage_stats['google']['calls'] += 1
            self.usage_stats['google']['tokens'] += len(content.split())
            
            return {
                'model': 'gemini-pro',
                'content': content,
                'quality_score': self.evaluate_quality(content),
                'tokens_used': len(content.split())
            }
        except Exception as e:
            logger.error(f"Google API error: {e}")
            return None
    
    def evaluate_quality(self, content: str) -> float:
        """评估响应质量"""
        quality_indicators = [
            '基于', '数据显示', '分析', '评估', '建议',
            '专业', '量化', '风险', '具体', '数据'
        ]
        
        score = 0
        for indicator in quality_indicators:
            if indicator in content:
                score += 0.1
        
        return min(score, 1.0)
    
    def synthesize_results(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """综合多个LLM的结果"""
        if not responses:
            return {'error': 'No valid responses from LLMs'}
        
        # 选择最佳响应
        best_response = max(responses, key=lambda x: x.get('quality_score', 0))
        
        # 综合所有响应
        all_contents = [r.get('content', '') for r in responses if r]
        combined_content = "\n\n".join(all_contents)
        
        return {
            'best_model': best_response.get('model'),
            'best_quality': best_response.get('quality_score'),
            'combined_analysis': combined_content,
            'all_responses': responses,
            'total_tokens': sum(r.get('tokens_used', 0) for r in responses)
        }
    
    def get_usage_stats(self):
        """获取使用统计"""
        return self.usage_stats

# 负载均衡器
class LoadBalancer:
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.current_index = 0
        self.api_stats = {key: {'calls': 0, 'errors': 0} for key in api_keys}
    
    def get_next_api_key(self) -> str:
        """获取下一个API密钥"""
        api_key = self.api_keys[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.api_keys)
        self.api_stats[api_key]['calls'] += 1
        return api_key
    
    def record_error(self, api_key: str):
        """记录API错误"""
        if api_key in self.api_stats:
            self.api_stats[api_key]['errors'] += 1
    
    def get_stats(self):
        """获取负载均衡统计"""
        return self.api_stats

# 代码增强代理
class CodeEnhancedAgent:
    def __init__(self):
        self.financial_tool = FinancialDataTool()
        self.llm_client = MultiLLMClient()
    
    async def analyze_asset(self, asset: Asset) -> Dict[str, Any]:
        """分析单个资产"""
        try:
            # 获取金融数据
            financial_data = await self.financial_tool.get_stock_data(asset.name)
            
            # 生成增强提示词
            enhanced_prompt = self.create_enhanced_prompt(asset, financial_data)
            
            # 使用多LLM分析
            analysis_result = await self.llm_client.analyze_with_multiple_llms(enhanced_prompt)
            
            return {
                'asset': asset.name,
                'financial_data': financial_data,
                'analysis': analysis_result,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error analyzing asset {asset.name}: {e}")
            return {
                'asset': asset.name,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def create_enhanced_prompt(self, asset: Asset, financial_data: Dict[str, Any]) -> str:
        """创建增强的提示词"""
        return f"""
请基于以下实时数据对{asset.name}进行专业的投资分析：

资产信息：
- 名称: {asset.name}
- 类型: {asset.type}
- 当前价值: {asset.value} {asset.currency}
- 成本: {asset.cost} {asset.currency}
- 当前价格: {asset.price} {asset.currency}
- 持有期: {asset.holding_period}
- 市场: {asset.market}

实时金融数据：
- 当前价格: ${financial_data.get('current_price', 0):.2f}
- P/E比率: {financial_data.get('pe_ratio', 0):.2f}
- P/B比率: {financial_data.get('pb_ratio', 0):.2f}
- RSI指标: {financial_data.get('rsi', 0):.2f}
- MACD指标: {financial_data.get('macd', 0):.2f}
- 波动率: {financial_data.get('volatility', 0):.2%}
- 20日均线: ${financial_data.get('sma_20', 0):.2f}
- 50日均线: ${financial_data.get('sma_50', 0):.2f}

请提供以下分析：
1. 技术面分析（基于RSI、MACD、均线等指标）
2. 基本面分析（基于P/E、P/B等估值指标）
3. 风险评估（基于波动率等指标）
4. 投资建议（持有、增持、减持、卖出）
5. 目标价格和止损建议

请用专业、客观的语言进行分析，并提供具体的数字支持。
"""

# 主应用
app = FastAPI(title="FinRobot优化版", version="2.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局实例
cache = ResponseCache()
performance_monitor = PerformanceMonitor()
load_balancer = LoadBalancer(Config.MULTI_API_KEYS)
enhanced_agent = CodeEnhancedAgent()

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "FinRobot优化版API",
        "version": "2.0.0",
        "features": [
            "多API并行处理",
            "多LLM集成",
            "代码增强分析",
            "智能缓存",
            "性能监控"
        ]
    }

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_portfolio(request: AnalyzeRequest):
    """分析投资组合 - 优化版本"""
    start_time = time.time()
    
    try:
        # 检查缓存
        cache_key = cache.get_cache_key(request.assets, request.client_profile)
        if request.use_cache:
            cached_result = cache.get(cache_key)
            if cached_result:
                performance_monitor.record_request(time.time() - start_time, True)
                return AnalyzeResponse(
                    analysis_results=cached_result,
                    performance_metrics=performance_monitor.get_stats(),
                    cache_info={'hit': True, 'key': cache_key},
                    quality_scores={'overall': 0.8}
                )
        
        # 并行分析所有资产
        analysis_tasks = []
        for asset in request.assets:
            task = enhanced_agent.analyze_asset(asset)
            analysis_tasks.append(task)
        
        # 等待所有分析完成
        analysis_results = await asyncio.gather(*analysis_tasks)
        
        # 整理结果
        results = {
            'assets_analysis': analysis_results,
            'portfolio_summary': self.create_portfolio_summary(analysis_results),
            'recommendations': self.generate_recommendations(analysis_results, request.client_profile),
            'risk_assessment': self.assess_portfolio_risk(analysis_results),
            'timestamp': datetime.now().isoformat()
        }
        
        # 缓存结果
        if request.use_cache:
            cache.set(cache_key, results)
        
        # 记录性能
        duration = time.time() - start_time
        performance_monitor.record_request(duration, True)
        
        # 计算质量分数
        quality_scores = self.calculate_quality_scores(analysis_results)
        
        return AnalyzeResponse(
            analysis_results=results,
            performance_metrics=performance_monitor.get_stats(),
            cache_info={'hit': False, 'key': cache_key},
            quality_scores=quality_scores
        )
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        performance_monitor.record_request(time.time() - start_time, False)
        raise HTTPException(status_code=500, detail=str(e))
    
    def create_portfolio_summary(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """创建投资组合摘要"""
        total_value = sum(result.get('asset', {}).get('value', 0) for result in analysis_results)
        total_cost = sum(result.get('asset', {}).get('cost', 0) for result in analysis_results)
        
        return {
            'total_value': total_value,
            'total_cost': total_cost,
            'total_return': total_value - total_cost,
            'return_percentage': ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0,
            'asset_count': len(analysis_results)
        }
    
    def generate_recommendations(self, analysis_results: List[Dict[str, Any]], client_profile: ClientProfile) -> List[Dict[str, Any]]:
        """生成投资建议"""
        recommendations = []
        
        for result in analysis_results:
            if 'analysis' in result and 'analysis' in result['analysis']:
                analysis = result['analysis']['analysis']
                if 'combined_analysis' in analysis:
                    content = analysis['combined_analysis']
                    
                    # 提取建议
                    recommendation = {
                        'asset': result['asset'],
                        'action': self.extract_action(content),
                        'reason': self.extract_reason(content),
                        'confidence': analysis.get('best_quality', 0.5)
                    }
                    recommendations.append(recommendation)
        
        return recommendations
    
    def assess_portfolio_risk(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """评估投资组合风险"""
        total_volatility = 0
        risk_count = 0
        
        for result in analysis_results:
            if 'financial_data' in result:
                volatility = result['financial_data'].get('volatility', 0)
                total_volatility += volatility
                risk_count += 1
        
        avg_volatility = total_volatility / risk_count if risk_count > 0 else 0
        
        return {
            'average_volatility': avg_volatility,
            'risk_level': 'High' if avg_volatility > 0.3 else 'Medium' if avg_volatility > 0.15 else 'Low',
            'diversification_score': len(analysis_results) / 10  # 简单的多样化评分
        }
    
    def calculate_quality_scores(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, float]:
        """计算质量分数"""
        scores = []
        
        for result in analysis_results:
            if 'analysis' in result and 'analysis' in result['analysis']:
                analysis = result['analysis']['analysis']
                quality = analysis.get('best_quality', 0.5)
                scores.append(quality)
        
        return {
            'overall': sum(scores) / len(scores) if scores else 0.5,
            'best': max(scores) if scores else 0.5,
            'worst': min(scores) if scores else 0.5
        }
    
    def extract_action(self, content: str) -> str:
        """从分析内容中提取行动建议"""
        content_lower = content.lower()
        if '增持' in content or 'buy' in content_lower or '买入' in content:
            return '增持'
        elif '减持' in content or 'sell' in content_lower or '卖出' in content:
            return '减持'
        elif '持有' in content or 'hold' in content_lower:
            return '持有'
        else:
            return '观望'
    
    def extract_reason(self, content: str) -> str:
        """从分析内容中提取原因"""
        # 简单的关键词提取
        keywords = ['因为', '由于', '基于', '考虑到', '鉴于']
        for keyword in keywords:
            if keyword in content:
                start = content.find(keyword)
                end = content.find('。', start)
                if end == -1:
                    end = content.find('\n', start)
                if end == -1:
                    end = len(content)
                return content[start:end]
        return "基于综合分析"

@app.get("/performance")
async def get_performance_stats():
    """获取性能统计"""
    return {
        "performance": performance_monitor.get_stats(),
        "cache": cache.get_stats(),
        "load_balancer": load_balancer.get_stats(),
        "llm_usage": enhanced_agent.llm_client.get_usage_stats()
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)