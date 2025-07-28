# 代码增强的Agent系统
# 集成多种工具和API来提升分析能力

import json
import time
import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf
import talib
from datetime import datetime, timedelta

@dataclass
class ToolResult:
    """工具执行结果"""
    tool_name: str
    success: bool
    data: Any
    error: Optional[str] = None
    execution_time: float = 0.0

class FinancialDataTool:
    """金融数据工具"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 3600  # 1小时缓存
    
    async def get_stock_data(self, symbol: str, period: str = "1y") -> ToolResult:
        """获取股票数据"""
        start_time = time.time()
        
        try:
            # 使用yfinance获取数据
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return ToolResult(
                    tool_name="stock_data",
                    success=False,
                    data=None,
                    error=f"No data found for {symbol}",
                    execution_time=time.time() - start_time
                )
            
            # 计算技术指标
            hist['SMA_20'] = talib.SMA(hist['Close'], timeperiod=20)
            hist['SMA_50'] = talib.SMA(hist['Close'], timeperiod=50)
            hist['RSI'] = talib.RSI(hist['Close'], timeperiod=14)
            hist['MACD'], hist['MACD_signal'], hist['MACD_hist'] = talib.MACD(hist['Close'])
            
            # 计算波动率
            hist['Returns'] = hist['Close'].pct_change()
            hist['Volatility'] = hist['Returns'].rolling(window=20).std() * np.sqrt(252)
            
            result_data = {
                'symbol': symbol,
                'current_price': hist['Close'].iloc[-1],
                'price_change': hist['Close'].iloc[-1] - hist['Close'].iloc[-2],
                'price_change_pct': ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100,
                'sma_20': hist['SMA_20'].iloc[-1],
                'sma_50': hist['SMA_50'].iloc[-1],
                'rsi': hist['RSI'].iloc[-1],
                'volatility': hist['Volatility'].iloc[-1],
                'volume': hist['Volume'].iloc[-1],
                'high_52w': hist['High'].max(),
                'low_52w': hist['Low'].min(),
                'data_points': len(hist)
            }
            
            return ToolResult(
                tool_name="stock_data",
                success=True,
                data=result_data,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ToolResult(
                tool_name="stock_data",
                success=False,
                data=None,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def get_financial_ratios(self, symbol: str) -> ToolResult:
        """获取财务比率"""
        start_time = time.time()
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            ratios = {
                'symbol': symbol,
                'pe_ratio': info.get('trailingPE', None),
                'pb_ratio': info.get('priceToBook', None),
                'ps_ratio': info.get('priceToSalesTrailing12Months', None),
                'dividend_yield': info.get('dividendYield', None),
                'roe': info.get('returnOnEquity', None),
                'roa': info.get('returnOnAssets', None),
                'debt_to_equity': info.get('debtToEquity', None),
                'current_ratio': info.get('currentRatio', None),
                'profit_margin': info.get('profitMargins', None),
                'revenue_growth': info.get('revenueGrowth', None),
                'earnings_growth': info.get('earningsGrowth', None)
            }
            
            return ToolResult(
                tool_name="financial_ratios",
                success=True,
                data=ratios,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ToolResult(
                tool_name="financial_ratios",
                success=False,
                data=None,
                error=str(e),
                execution_time=time.time() - start_time
            )

class MarketSentimentTool:
    """市场情绪工具"""
    
    def __init__(self):
        self.api_keys = self._load_api_keys()
    
    def _load_api_keys(self) -> Dict[str, str]:
        """加载API密钥"""
        try:
            with open('config_api_keys', 'r') as f:
                return json.load(f)
        except:
            return {}
    
    async def get_news_sentiment(self, symbol: str) -> ToolResult:
        """获取新闻情绪"""
        start_time = time.time()
        
        try:
            # 这里可以集成新闻API，如NewsAPI、Alpha Vantage等
            # 为了演示，返回模拟数据
            sentiment_data = {
                'symbol': symbol,
                'sentiment_score': np.random.uniform(-1, 1),
                'news_count': np.random.randint(10, 100),
                'positive_news': np.random.randint(5, 50),
                'negative_news': np.random.randint(5, 50),
                'neutral_news': np.random.randint(5, 50),
                'last_updated': datetime.now().isoformat()
            }
            
            return ToolResult(
                tool_name="news_sentiment",
                success=True,
                data=sentiment_data,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ToolResult(
                tool_name="news_sentiment",
                success=False,
                data=None,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def get_social_sentiment(self, symbol: str) -> ToolResult:
        """获取社交媒体情绪"""
        start_time = time.time()
        
        try:
            # 这里可以集成Twitter、Reddit等社交媒体API
            social_data = {
                'symbol': symbol,
                'twitter_mentions': np.random.randint(100, 1000),
                'reddit_mentions': np.random.randint(50, 500),
                'sentiment_score': np.random.uniform(-1, 1),
                'trending_score': np.random.uniform(0, 1),
                'last_updated': datetime.now().isoformat()
            }
            
            return ToolResult(
                tool_name="social_sentiment",
                success=True,
                data=social_data,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ToolResult(
                tool_name="social_sentiment",
                success=False,
                data=None,
                error=str(e),
                execution_time=time.time() - start_time
            )

class TechnicalAnalysisTool:
    """技术分析工具"""
    
    def __init__(self):
        self.indicators = {}
    
    async def calculate_technical_indicators(self, symbol: str, period: str = "1y") -> ToolResult:
        """计算技术指标"""
        start_time = time.time()
        
        try:
            # 获取股票数据
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return ToolResult(
                    tool_name="technical_analysis",
                    success=False,
                    data=None,
                    error=f"No data found for {symbol}",
                    execution_time=time.time() - start_time
                )
            
            # 计算各种技术指标
            close_prices = hist['Close'].values
            high_prices = hist['High'].values
            low_prices = hist['Low'].values
            volume = hist['Volume'].values
            
            technical_data = {
                'symbol': symbol,
                'current_price': close_prices[-1],
                'sma_20': talib.SMA(close_prices, timeperiod=20)[-1],
                'sma_50': talib.SMA(close_prices, timeperiod=50)[-1],
                'ema_12': talib.EMA(close_prices, timeperiod=12)[-1],
                'ema_26': talib.EMA(close_prices, timeperiod=26)[-1],
                'rsi': talib.RSI(close_prices, timeperiod=14)[-1],
                'macd': talib.MACD(close_prices)[0][-1],
                'macd_signal': talib.MACD(close_prices)[1][-1],
                'macd_histogram': talib.MACD(close_prices)[2][-1],
                'bb_upper': talib.BBANDS(close_prices)[0][-1],
                'bb_middle': talib.BBANDS(close_prices)[1][-1],
                'bb_lower': talib.BBANDS(close_prices)[2][-1],
                'stoch_k': talib.STOCH(high_prices, low_prices, close_prices)[0][-1],
                'stoch_d': talib.STOCH(high_prices, low_prices, close_prices)[1][-1],
                'adx': talib.ADX(high_prices, low_prices, close_prices, timeperiod=14)[-1],
                'obv': talib.OBV(close_prices, volume)[-1],
                'volume_sma': talib.SMA(volume, timeperiod=20)[-1],
                'atr': talib.ATR(high_prices, low_prices, close_prices, timeperiod=14)[-1]
            }
            
            # 计算趋势信号
            technical_data['trend_signal'] = self._calculate_trend_signal(technical_data)
            technical_data['momentum_signal'] = self._calculate_momentum_signal(technical_data)
            technical_data['volatility_signal'] = self._calculate_volatility_signal(technical_data)
            
            return ToolResult(
                tool_name="technical_analysis",
                success=True,
                data=technical_data,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ToolResult(
                tool_name="technical_analysis",
                success=False,
                data=None,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _calculate_trend_signal(self, data: Dict) -> str:
        """计算趋势信号"""
        if data['current_price'] > data['sma_20'] > data['sma_50']:
            return "strong_uptrend"
        elif data['current_price'] > data['sma_20']:
            return "uptrend"
        elif data['current_price'] < data['sma_20'] < data['sma_50']:
            return "strong_downtrend"
        elif data['current_price'] < data['sma_20']:
            return "downtrend"
        else:
            return "sideways"
    
    def _calculate_momentum_signal(self, data: Dict) -> str:
        """计算动量信号"""
        if data['rsi'] > 70:
            return "overbought"
        elif data['rsi'] < 30:
            return "oversold"
        else:
            return "neutral"
    
    def _calculate_volatility_signal(self, data: Dict) -> str:
        """计算波动率信号"""
        bb_position = (data['current_price'] - data['bb_lower']) / (data['bb_upper'] - data['bb_lower'])
        
        if bb_position > 0.8:
            return "high_volatility"
        elif bb_position < 0.2:
            return "low_volatility"
        else:
            return "normal_volatility"

class RiskAssessmentTool:
    """风险评估工具"""
    
    def __init__(self):
        self.risk_models = {}
    
    async def calculate_risk_metrics(self, symbol: str, portfolio_data: Dict) -> ToolResult:
        """计算风险指标"""
        start_time = time.time()
        
        try:
            # 获取历史数据
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2y")
            
            if hist.empty:
                return ToolResult(
                    tool_name="risk_assessment",
                    success=False,
                    data=None,
                    error=f"No data found for {symbol}",
                    execution_time=time.time() - start_time
                )
            
            # 计算风险指标
            returns = hist['Close'].pct_change().dropna()
            
            risk_metrics = {
                'symbol': symbol,
                'volatility': returns.std() * np.sqrt(252),
                'sharpe_ratio': (returns.mean() * 252) / (returns.std() * np.sqrt(252)),
                'max_drawdown': self._calculate_max_drawdown(hist['Close']),
                'var_95': np.percentile(returns, 5),
                'var_99': np.percentile(returns, 1),
                'skewness': returns.skew(),
                'kurtosis': returns.kurtosis(),
                'beta': self._calculate_beta(returns, symbol),
                'correlation': self._calculate_correlation(returns, portfolio_data),
                'risk_score': self._calculate_risk_score(returns)
            }
            
            return ToolResult(
                tool_name="risk_assessment",
                success=True,
                data=risk_metrics,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ToolResult(
                tool_name="risk_assessment",
                success=False,
                data=None,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """计算最大回撤"""
        peak = prices.expanding().max()
        drawdown = (prices - peak) / peak
        return drawdown.min()
    
    def _calculate_beta(self, returns: pd.Series, symbol: str) -> float:
        """计算Beta值"""
        try:
            # 获取市场指数数据（这里用SPY作为市场代理）
            market = yf.Ticker("SPY")
            market_returns = market.history(period="2y")['Close'].pct_change().dropna()
            
            # 对齐数据
            aligned_returns = returns.align(market_returns, join='inner')[0]
            aligned_market = returns.align(market_returns, join='inner')[1]
            
            # 计算Beta
            covariance = np.cov(aligned_returns, aligned_market)[0, 1]
            market_variance = np.var(aligned_market)
            
            return covariance / market_variance if market_variance != 0 else 1.0
        except:
            return 1.0
    
    def _calculate_correlation(self, returns: pd.Series, portfolio_data: Dict) -> float:
        """计算与投资组合的相关性"""
        # 这里可以计算与现有投资组合的相关性
        # 为了演示，返回随机值
        return np.random.uniform(-1, 1)
    
    def _calculate_risk_score(self, returns: pd.Series) -> float:
        """计算综合风险评分"""
        volatility_score = returns.std() * np.sqrt(252)
        drawdown_score = abs(self._calculate_max_drawdown(returns.cumsum()))
        var_score = abs(np.percentile(returns, 5))
        
        # 综合风险评分 (0-100)
        risk_score = (volatility_score * 0.4 + drawdown_score * 0.3 + var_score * 0.3) * 100
        return min(risk_score, 100)

class CodeEnhancedAgent:
    """代码增强的Agent"""
    
    def __init__(self, agent_name: str, base_prompt: str):
        self.agent_name = agent_name
        self.base_prompt = base_prompt
        self.financial_tool = FinancialDataTool()
        self.sentiment_tool = MarketSentimentTool()
        self.technical_tool = TechnicalAnalysisTool()
        self.risk_tool = RiskAssessmentTool()
        
    async def analyze_with_tools(self, symbol: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用多种工具进行分析"""
        start_time = time.time()
        
        # 并行执行所有工具
        tasks = [
            self.financial_tool.get_stock_data(symbol),
            self.financial_tool.get_financial_ratios(symbol),
            self.sentiment_tool.get_news_sentiment(symbol),
            self.sentiment_tool.get_social_sentiment(symbol),
            self.technical_tool.calculate_technical_indicators(symbol),
            self.risk_tool.calculate_risk_metrics(symbol, context)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 整理结果
        analysis_data = {
            'symbol': symbol,
            'analysis_time': time.time() - start_time,
            'tools_used': [],
            'data_summary': {}
        }
        
        for result in results:
            if isinstance(result, ToolResult) and result.success:
                analysis_data['tools_used'].append(result.tool_name)
                analysis_data['data_summary'][result.tool_name] = result.data
        
        return analysis_data
    
    def generate_enhanced_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """生成增强的提示词"""
        enhanced_prompt = self.base_prompt + "\n\n"
        
        # 添加数据驱动的分析要求
        if 'stock_data' in analysis_data['data_summary']:
            stock_data = analysis_data['data_summary']['stock_data']
            enhanced_prompt += f"""
当前股价数据：
- 当前价格: ${stock_data['current_price']:.2f}
- 价格变化: {stock_data['price_change_pct']:.2f}%
- 52周最高: ${stock_data['high_52w']:.2f}
- 52周最低: ${stock_data['low_52w']:.2f}
- 波动率: {stock_data['volatility']:.2f}
"""
        
        if 'financial_ratios' in analysis_data['data_summary']:
            ratios = analysis_data['data_summary']['financial_ratios']
            enhanced_prompt += f"""
财务比率数据：
- P/E比率: {ratios['pe_ratio']:.2f if ratios['pe_ratio'] else 'N/A'}
- P/B比率: {ratios['pb_ratio']:.2f if ratios['pb_ratio'] else 'N/A'}
- 股息率: {ratios['dividend_yield']:.2f}% if ratios['dividend_yield'] else 'N/A'}
- ROE: {ratios['roe']:.2f}% if ratios['roe'] else 'N/A'}
- ROA: {ratios['roa']:.2f}% if ratios['roa'] else 'N/A'}
"""
        
        if 'technical_analysis' in analysis_data['data_summary']:
            tech_data = analysis_data['data_summary']['technical_analysis']
            enhanced_prompt += f"""
技术分析数据：
- RSI: {tech_data['rsi']:.2f}
- MACD: {tech_data['macd']:.4f}
- 趋势信号: {tech_data['trend_signal']}
- 动量信号: {tech_data['momentum_signal']}
- 波动率信号: {tech_data['volatility_signal']}
"""
        
        if 'risk_assessment' in analysis_data['data_summary']:
            risk_data = analysis_data['data_summary']['risk_assessment']
            enhanced_prompt += f"""
风险评估数据：
- 波动率: {risk_data['volatility']:.2f}
- 夏普比率: {risk_data['sharpe_ratio']:.2f}
- 最大回撤: {risk_data['max_drawdown']:.2f}%
- Beta值: {risk_data['beta']:.2f}
- 风险评分: {risk_data['risk_score']:.1f}/100
"""
        
        enhanced_prompt += """
请基于以上实时数据进行分析，确保分析结果：
1. 基于具体数据而非泛泛而谈
2. 提供量化的分析结论
3. 结合技术面和基本面
4. 考虑风险因素
5. 给出具体的操作建议
"""
        
        return enhanced_prompt

# 使用示例
async def main():
    # 创建代码增强的agent
    value_agent = CodeEnhancedAgent(
        "Value_Factor_Analyst",
        "你是价值因子分析师，请基于提供的实时数据进行分析..."
    )
    
    # 使用工具进行分析
    analysis_data = await value_agent.analyze_with_tools("AAPL", {})
    
    # 生成增强的提示词
    enhanced_prompt = value_agent.generate_enhanced_prompt(analysis_data)
    
    print("增强的提示词:")
    print(enhanced_prompt)
    
    print("\n分析数据摘要:")
    print(json.dumps(analysis_data, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())