# 多LLM集成系统
# 集成Claude、GPT等多种LLM和工具

import json
import time
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import openai
from anthropic import Anthropic
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor

@dataclass
class LLMResponse:
    """LLM响应结果"""
    model: str
    content: str
    tokens_used: int
    response_time: float
    cost: float
    quality_score: Optional[float] = None

class MultiLLMClient:
    """多LLM客户端"""
    
    def __init__(self):
        self.clients = {}
        self.api_keys = self._load_api_keys()
        self._initialize_clients()
    
    def _load_api_keys(self) -> Dict[str, str]:
        """加载API密钥"""
        try:
            with open('config_api_keys', 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _initialize_clients(self):
        """初始化各种LLM客户端"""
        # OpenAI GPT
        if 'openai_api_key' in self.api_keys:
            openai.api_key = self.api_keys['openai_api_key']
            self.clients['gpt-4'] = {
                'client': openai,
                'model': 'gpt-4',
                'max_tokens': 2000,
                'temperature': 0.1
            }
            self.clients['gpt-3.5-turbo'] = {
                'client': openai,
                'model': 'gpt-3.5-turbo',
                'max_tokens': 2000,
                'temperature': 0.1
            }
        
        # Anthropic Claude
        if 'anthropic_api_key' in self.api_keys:
            self.clients['claude-3-sonnet'] = {
                'client': Anthropic(api_key=self.api_keys['anthropic_api_key']),
                'model': 'claude-3-sonnet-20240229',
                'max_tokens': 2000,
                'temperature': 0.1
            }
            self.clients['claude-3-haiku'] = {
                'client': Anthropic(api_key=self.api_keys['anthropic_api_key']),
                'model': 'claude-3-haiku-20240307',
                'max_tokens': 2000,
                'temperature': 0.1
            }
        
        # Google Gemini
        if 'google_api_key' in self.api_keys:
            genai.configure(api_key=self.api_keys['google_api_key'])
            self.clients['gemini-pro'] = {
                'client': genai,
                'model': 'gemini-pro',
                'max_tokens': 2000,
                'temperature': 0.1
            }
        
        # DeepSeek
        if 'deepseek_api_key' in self.api_keys:
            self.clients['deepseek-chat'] = {
                'client': openai,
                'model': 'deepseek-chat',
                'base_url': 'https://api.deepseek.com/v1',
                'max_tokens': 2000,
                'temperature': 0.1
            }
    
    async def call_llm(self, model: str, prompt: str, context: Dict[str, Any] = None) -> LLMResponse:
        """调用指定的LLM"""
        start_time = time.time()
        
        if model not in self.clients:
            raise ValueError(f"Model {model} not available")
        
        client_config = self.clients[model]
        
        try:
            if 'anthropic' in model.lower():
                # Claude API
                response = await self._call_claude(client_config, prompt, context)
            elif 'gemini' in model.lower():
                # Gemini API
                response = await self._call_gemini(client_config, prompt, context)
            else:
                # OpenAI compatible API
                response = await self._call_openai(client_config, prompt, context)
            
            response_time = time.time() - start_time
            
            return LLMResponse(
                model=model,
                content=response['content'],
                tokens_used=response.get('tokens_used', 0),
                response_time=response_time,
                cost=self._calculate_cost(model, response.get('tokens_used', 0)),
                quality_score=self._evaluate_response_quality(response['content'])
            )
            
        except Exception as e:
            return LLMResponse(
                model=model,
                content=f"Error: {str(e)}",
                tokens_used=0,
                response_time=time.time() - start_time,
                cost=0.0,
                quality_score=0.0
            )
    
    async def _call_claude(self, client_config: Dict, prompt: str, context: Dict = None) -> Dict:
        """调用Claude API"""
        client = client_config['client']
        
        # 构建消息
        messages = []
        if context and 'system_prompt' in context:
            messages.append({"role": "user", "content": context['system_prompt']})
        
        messages.append({"role": "user", "content": prompt})
        
        response = client.messages.create(
            model=client_config['model'],
            max_tokens=client_config['max_tokens'],
            temperature=client_config['temperature'],
            messages=messages
        )
        
        return {
            'content': response.content[0].text,
            'tokens_used': response.usage.input_tokens + response.usage.output_tokens
        }
    
    async def _call_gemini(self, client_config: Dict, prompt: str, context: Dict = None) -> Dict:
        """调用Gemini API"""
        client = client_config['client']
        model = client.GenerativeModel(client_config['model'])
        
        # 构建提示词
        full_prompt = prompt
        if context and 'system_prompt' in context:
            full_prompt = context['system_prompt'] + "\n\n" + prompt
        
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=client_config['max_tokens'],
                temperature=client_config['temperature']
            )
        )
        
        return {
            'content': response.text,
            'tokens_used': len(full_prompt.split()) + len(response.text.split())  # 估算
        }
    
    async def _call_openai(self, client_config: Dict, prompt: str, context: Dict = None) -> Dict:
        """调用OpenAI兼容API"""
        client = client_config['client']
        
        # 构建消息
        messages = []
        if context and 'system_prompt' in context:
            messages.append({"role": "system", "content": context['system_prompt']})
        
        messages.append({"role": "user", "content": prompt})
        
        # 设置API参数
        api_params = {
            "model": client_config['model'],
            "messages": messages,
            "max_tokens": client_config['max_tokens'],
            "temperature": client_config['temperature']
        }
        
        # 如果是DeepSeek，需要设置base_url
        if 'base_url' in client_config:
            api_params['base_url'] = client_config['base_url']
        
        response = client.ChatCompletion.create(**api_params)
        
        return {
            'content': response.choices[0].message.content,
            'tokens_used': response.usage.total_tokens
        }
    
    def _calculate_cost(self, model: str, tokens: int) -> float:
        """计算API调用成本"""
        # 简化的成本计算（实际应该根据各API的定价）
        cost_per_1k_tokens = {
            'gpt-4': 0.03,
            'gpt-3.5-turbo': 0.002,
            'claude-3-sonnet': 0.015,
            'claude-3-haiku': 0.0025,
            'gemini-pro': 0.001,
            'deepseek-chat': 0.002
        }
        
        return (tokens / 1000) * cost_per_1k_tokens.get(model, 0.01)
    
    def _evaluate_response_quality(self, content: str) -> float:
        """评估响应质量"""
        # 简单的质量评估
        quality_indicators = [
            '专业分析', '通俗解释', '可操作建议', '风险提示',
            '基于', '数据显示', '分析', '评估', '建议'
        ]
        
        score = 0
        for indicator in quality_indicators:
            if indicator in content:
                score += 0.1
        
        return min(score, 1.0)

class ToolIntegrationManager:
    """工具集成管理器"""
    
    def __init__(self):
        self.tools = {}
        self._register_tools()
    
    def _register_tools(self):
        """注册各种工具"""
        # 金融数据工具
        self.tools['financial_data'] = {
            'description': '获取股票价格、财务数据等',
            'function': self._get_financial_data,
            'required_params': ['symbol']
        }
        
        # 技术分析工具
        self.tools['technical_analysis'] = {
            'description': '计算技术指标',
            'function': self._get_technical_analysis,
            'required_params': ['symbol']
        }
        
        # 新闻情绪工具
        self.tools['news_sentiment'] = {
            'description': '获取新闻情绪分析',
            'function': self._get_news_sentiment,
            'required_params': ['symbol']
        }
        
        # 风险评估工具
        self.tools['risk_assessment'] = {
            'description': '计算风险指标',
            'function': self._get_risk_assessment,
            'required_params': ['symbol']
        }
    
    async def _get_financial_data(self, symbol: str) -> Dict[str, Any]:
        """获取金融数据"""
        # 这里应该调用实际的金融数据API
        return {
            'symbol': symbol,
            'current_price': 150.0,
            'pe_ratio': 25.5,
            'pb_ratio': 3.2,
            'dividend_yield': 2.1,
            'market_cap': 2500000000
        }
    
    async def _get_technical_analysis(self, symbol: str) -> Dict[str, Any]:
        """获取技术分析"""
        return {
            'symbol': symbol,
            'rsi': 65.5,
            'macd': 0.25,
            'sma_20': 148.5,
            'sma_50': 145.2,
            'trend': 'uptrend'
        }
    
    async def _get_news_sentiment(self, symbol: str) -> Dict[str, Any]:
        """获取新闻情绪"""
        return {
            'symbol': symbol,
            'sentiment_score': 0.3,
            'news_count': 45,
            'positive_ratio': 0.6
        }
    
    async def _get_risk_assessment(self, symbol: str) -> Dict[str, Any]:
        """获取风险评估"""
        return {
            'symbol': symbol,
            'volatility': 0.25,
            'beta': 1.1,
            'sharpe_ratio': 0.8,
            'max_drawdown': -0.15
        }

class EnhancedAgent:
    """增强的Agent，集成多种LLM和工具"""
    
    def __init__(self, agent_name: str, base_prompt: str):
        self.agent_name = agent_name
        self.base_prompt = base_prompt
        self.llm_client = MultiLLMClient()
        self.tool_manager = ToolIntegrationManager()
        self.performance_history = []
    
    async def analyze_with_enhancement(self, symbol: str, analysis_type: str, 
                                     preferred_models: List[str] = None) -> Dict[str, Any]:
        """使用增强功能进行分析"""
        start_time = time.time()
        
        # 1. 获取工具数据
        tool_data = await self._gather_tool_data(symbol)
        
        # 2. 生成增强提示词
        enhanced_prompt = self._create_enhanced_prompt(symbol, tool_data, analysis_type)
        
        # 3. 使用多个LLM进行分析
        if not preferred_models:
            preferred_models = ['claude-3-sonnet', 'gpt-4', 'deepseek-chat']
        
        llm_responses = await self._call_multiple_llms(enhanced_prompt, preferred_models)
        
        # 4. 综合多个LLM的结果
        final_result = self._synthesize_results(llm_responses, tool_data)
        
        # 5. 记录性能
        self._record_performance(start_time, len(llm_responses))
        
        return final_result
    
    async def _gather_tool_data(self, symbol: str) -> Dict[str, Any]:
        """收集工具数据"""
        tool_tasks = []
        for tool_name, tool_config in self.tool_manager.tools.items():
            task = tool_config['function'](symbol)
            tool_tasks.append((tool_name, task))
        
        results = {}
        for tool_name, task in tool_tasks:
            try:
                result = await task
                results[tool_name] = result
            except Exception as e:
                results[tool_name] = {'error': str(e)}
        
        return results
    
    def _create_enhanced_prompt(self, symbol: str, tool_data: Dict[str, Any], 
                               analysis_type: str) -> str:
        """创建增强的提示词"""
        prompt = f"{self.base_prompt}\n\n"
        
        # 添加工具数据
        prompt += f"分析目标：{symbol} 的 {analysis_type} 分析\n\n"
        
        if 'financial_data' in tool_data:
            fd = tool_data['financial_data']
            prompt += f"财务数据：\n"
            prompt += f"- 当前价格: ${fd.get('current_price', 'N/A')}\n"
            prompt += f"- P/E比率: {fd.get('pe_ratio', 'N/A')}\n"
            prompt += f"- P/B比率: {fd.get('pb_ratio', 'N/A')}\n"
            prompt += f"- 股息率: {fd.get('dividend_yield', 'N/A')}%\n\n"
        
        if 'technical_analysis' in tool_data:
            ta = tool_data['technical_analysis']
            prompt += f"技术分析：\n"
            prompt += f"- RSI: {ta.get('rsi', 'N/A')}\n"
            prompt += f"- MACD: {ta.get('macd', 'N/A')}\n"
            prompt += f"- 趋势: {ta.get('trend', 'N/A')}\n\n"
        
        if 'news_sentiment' in tool_data:
            ns = tool_data['news_sentiment']
            prompt += f"市场情绪：\n"
            prompt += f"- 情绪评分: {ns.get('sentiment_score', 'N/A')}\n"
            prompt += f"- 新闻数量: {ns.get('news_count', 'N/A')}\n\n"
        
        if 'risk_assessment' in tool_data:
            ra = tool_data['risk_assessment']
            prompt += f"风险评估：\n"
            prompt += f"- 波动率: {ra.get('volatility', 'N/A')}\n"
            prompt += f"- Beta值: {ra.get('beta', 'N/A')}\n"
            prompt += f"- 夏普比率: {ra.get('sharpe_ratio', 'N/A')}\n\n"
        
        prompt += "请基于以上数据进行分析，确保：\n"
        prompt += "1. 分析基于具体数据\n"
        prompt += "2. 提供量化结论\n"
        prompt += "3. 考虑风险因素\n"
        prompt += "4. 给出具体建议\n"
        
        return prompt
    
    async def _call_multiple_llms(self, prompt: str, models: List[str]) -> List[LLMResponse]:
        """调用多个LLM"""
        tasks = []
        for model in models:
            if model in self.llm_client.clients:
                task = self.llm_client.call_llm(model, prompt)
                tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤掉异常结果
        valid_responses = []
        for response in responses:
            if isinstance(response, LLMResponse) and response.content and not response.content.startswith("Error"):
                valid_responses.append(response)
        
        return valid_responses
    
    def _synthesize_results(self, llm_responses: List[LLMResponse], 
                           tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """综合多个LLM的结果"""
        if not llm_responses:
            return {'error': 'No valid responses from LLMs'}
        
        # 按质量评分排序
        sorted_responses = sorted(llm_responses, key=lambda x: x.quality_score, reverse=True)
        
        # 选择最佳响应
        best_response = sorted_responses[0]
        
        # 如果有多个高质量响应，可以综合它们
        high_quality_responses = [r for r in sorted_responses if r.quality_score > 0.7]
        
        if len(high_quality_responses) > 1:
            # 综合多个高质量响应
            combined_content = self._combine_responses(high_quality_responses)
        else:
            combined_content = best_response.content
        
        return {
            'analysis': combined_content,
            'best_model': best_response.model,
            'quality_score': best_response.quality_score,
            'total_cost': sum(r.cost for r in llm_responses),
            'total_time': sum(r.response_time for r in llm_responses),
            'models_used': [r.model for r in llm_responses],
            'tool_data': tool_data
        }
    
    def _combine_responses(self, responses: List[LLMResponse]) -> str:
        """综合多个响应"""
        # 简单的综合策略：选择最长的响应
        return max(responses, key=lambda x: len(x.content)).content
    
    def _record_performance(self, start_time: float, num_models: int):
        """记录性能"""
        total_time = time.time() - start_time
        self.performance_history.append({
            'timestamp': time.time(),
            'total_time': total_time,
            'num_models': num_models,
            'avg_time_per_model': total_time / num_models if num_models > 0 else 0
        })

# 使用示例
async def main():
    # 创建增强的agent
    value_agent = EnhancedAgent(
        "Value_Factor_Analyst",
        "你是价值因子分析师，请进行专业的价值分析..."
    )
    
    # 进行分析
    result = await value_agent.analyze_with_enhancement(
        symbol="AAPL",
        analysis_type="价值因子分析",
        preferred_models=['claude-3-sonnet', 'gpt-4']
    )
    
    print("增强分析结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())