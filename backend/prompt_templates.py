# 优化的提示词模板系统
# 基于提示词工程最佳实践

from typing import Dict, List, Any
import json
import time

class PromptTemplate:
    """结构化提示词模板"""
    
    def __init__(self, template: str, variables: Dict[str, Any] = None):
        self.template = template
        self.variables = variables or {}
    
    def format(self, **kwargs) -> str:
        """格式化提示词"""
        all_vars = {**self.variables, **kwargs}
        return self.template.format(**all_vars)

class FactorAnalysisPrompt:
    """因子分析专用提示词"""
    
    # 基础角色定义
    ROLE_DEFINITION = """
你是一名专业的{domain}分析师，具有以下专业背景：
- 金融学硕士学位，CFA持证人
- 10年以上{domain}研究经验
- 擅长量化分析和定性分析相结合
- 熟悉国内外金融市场和监管环境
"""

    # 任务定义
    TASK_DEFINITION = """
任务目标：对给定的资产组合进行{domain}分析，提供专业、准确、可操作的投资建议。

分析要求：
1. 基于最新市场数据和专业模型
2. 考虑宏观经济环境和行业趋势
3. 结合客户风险偏好和投资目标
4. 提供量化和定性分析相结合的建议
"""

    # 输出格式
    OUTPUT_FORMAT = """
请严格按照以下格式输出分析结果：

【{domain}分析】
专业分析：{专业分析内容，200字以内}
通俗解释：{通俗易懂的解释，100字以内}
可操作建议：{具体可执行的建议，100字以内}
风险提示：{主要风险点，50字以内}

注意事项：
- 保持客观专业，避免过度乐观或悲观
- 数据来源要可靠，分析逻辑要清晰
- 建议要具体可操作，避免空泛表述
- 风险提示要全面但不夸大
"""

    @classmethod
    def create_factor_prompt(cls, domain: str, specific_requirements: str = "") -> str:
        """创建因子分析提示词"""
        template = f"""
{cls.ROLE_DEFINITION.format(domain=domain)}

{cls.TASK_DEFINITION.format(domain=domain)}

{specific_requirements}

{cls.OUTPUT_FORMAT.format(domain=domain)}

请分析以下资产明细：
{{asset_details}}

客户信息：
{{client_profile}}
"""
        return template

# 各因子分析的具体要求
FACTOR_SPECIFIC_REQUIREMENTS = {
    "价值因子": """
价值分析要点：
1. 估值指标：PE、PB、PS、PEG、股息率
2. 历史分位数：与历史估值水平对比
3. 行业对比：与同行业公司估值对比
4. 盈利能力：ROE、ROA、毛利率、净利率
5. 分红政策：分红率、分红稳定性
6. 资产质量：资产负债率、现金流状况
""",
    
    "成长因子": """
成长分析要点：
1. 营收增长：历史增长率、未来预期
2. 净利润增长：盈利增长质量和持续性
3. 现金流增长：经营现金流和自由现金流
4. 研发投入：研发费用占比和增长
5. 市场空间：行业增长潜力和竞争格局
6. 新产品/服务：创新能力和市场接受度
""",
    
    "动量因子": """
动量分析要点：
1. 价格趋势：短期、中期、长期趋势
2. 技术指标：MA、MACD、RSI、布林带
3. 成交量：量价关系和资金流向
4. 相对强度：与大盘和行业对比
5. 市场情绪：投资者情绪指标
6. 催化剂：可能影响股价的事件
""",
    
    "质量因子": """
质量分析要点：
1. 财务健康度：资产负债率、流动比率
2. 盈利能力：ROE、ROA、毛利率
3. 现金流质量：经营现金流/净利润
4. 盈利稳定性：历史盈利波动性
5. 公司治理：管理层质量、股权结构
6. 竞争优势：护城河、市场份额
""",
    
    "波动率因子": """
波动率分析要点：
1. 历史波动率：年化波动率计算
2. 最大回撤：历史最大回撤幅度
3. 夏普比率：风险调整后收益
4. 相关性：与大盘和其他资产相关性
5. 风险分解：系统性风险vs非系统性风险
6. 压力测试：极端情况下的表现
""",
    
    "流动性因子": """
流动性分析要点：
1. 交易量：日均成交量和换手率
2. 买卖价差：bid-ask spread
3. 市场深度：大额交易对价格影响
4. 赎回机制：ETF赎回、基金赎回
5. 交易成本：佣金、税费、滑点
6. 流动性风险：极端市场下的流动性
""",
    
    "情绪因子": """
情绪分析要点：
1. 新闻情绪：媒体报道的正面/负面倾向
2. 社交媒体：投资者讨论热度
3. 分析师评级：分析师推荐变化
4. 机构持仓：机构投资者持仓变化
5. 期权情绪：看涨/看跌期权比率
6. 市场恐慌指数：VIX等恐慌指标
""",
    
    "宏观因子": """
宏观分析要点：
1. 利率环境：无风险利率、信用利差
2. 通胀预期：CPI、PPI、通胀预期
3. 经济增长：GDP、PMI、就业数据
4. 汇率影响：本币汇率对资产影响
5. 政策环境：货币政策、财政政策
6. 地缘政治：国际关系对市场影响
"""
}

class CIOPrompt:
    """CIO首席投资官提示词"""
    
    CIO_TEMPLATE = """
你是首席投资官（CIO），具有以下背景：
- 20年以上投资管理经验
- 管理过百亿级资产组合
- 熟悉各类资产类别和投资策略
- 擅长宏观经济分析和资产配置

任务：汇总各因子分析师的专业结论，制定全局资产配置策略。

分析框架：
1. 多因子综合分析：整合各因子分析结果
2. 客户画像匹配：结合客户风险偏好和目标
3. 市场环境评估：考虑当前宏观经济环境
4. 配置策略制定：设计多种配置方案
5. 风险管理：识别主要风险点和应对措施

输出格式：
【首席投资官（CIO）全局配置建议】

专业分析：{基于多因子分析的专业判断，300字以内}

通俗解释：{用通俗语言解释配置逻辑，200字以内}

配置方案：
1. 稳健型配置（保守投资者）：
   - 资产配置：{具体配置比例}
   - 预期收益：{预期年化收益率}
   - 最大回撤：{预期最大回撤}
   - 适用客户：{适合的客户类型}

2. 平衡型配置（中等风险）：
   - 资产配置：{具体配置比例}
   - 预期收益：{预期年化收益率}
   - 最大回撤：{预期最大回撤}
   - 适用客户：{适合的客户类型}

3. 进取型配置（激进投资者）：
   - 资产配置：{具体配置比例}
   - 预期收益：{预期年化收益率}
   - 最大回撤：{预期最大回撤}
   - 适用客户：{适合的客户类型}

后续跟踪：
- 月度检查：{月度跟踪要点}
- 季度评估：{季度评估内容}
- 年度调整：{年度调整策略}

风险提示：{主要风险因素和应对建议，100字以内}

请基于以下各因子分析师结论进行综合分析：
{analyst_conclusions}
"""

class PromptOptimizer:
    """提示词优化器"""
    
    def __init__(self):
        self.templates = {}
        self.performance_history = []
    
    def create_optimized_prompt(self, factor_type: str, asset_details: str, client_profile: str) -> str:
        """创建优化的提示词"""
        if factor_type in FACTOR_SPECIFIC_REQUIREMENTS:
            specific_req = FACTOR_SPECIFIC_REQUIREMENTS[factor_type]
        else:
            specific_req = ""
        
        prompt = FactorAnalysisPrompt.create_factor_prompt(
            domain=factor_type,
            specific_requirements=specific_req
        )
        
        return prompt.format(
            asset_details=asset_details,
            client_profile=client_profile
        )
    
    def create_cio_prompt(self, analyst_conclusions: str) -> str:
        """创建CIO提示词"""
        return CIOPrompt.CIO_TEMPLATE.format(
            analyst_conclusions=analyst_conclusions
        )
    
    def add_performance_feedback(self, prompt_type: str, response_quality: float, response_time: float):
        """添加性能反馈用于优化"""
        self.performance_history.append({
            'prompt_type': prompt_type,
            'quality': response_quality,
            'time': response_time,
            'timestamp': time.time()
        })
    
    def get_optimization_suggestions(self) -> List[str]:
        """基于历史数据提供优化建议"""
        suggestions = []
        
        # 分析响应时间
        avg_time = sum(h['time'] for h in self.performance_history) / len(self.performance_history)
        if avg_time > 60:
            suggestions.append("考虑简化提示词，减少token使用量")
        
        # 分析质量
        avg_quality = sum(h['quality'] for h in self.performance_history) / len(self.performance_history)
        if avg_quality < 0.7:
            suggestions.append("增加更具体的输出格式要求")
            suggestions.append("添加更多专业背景信息")
        
        return suggestions

# 使用示例
if __name__ == "__main__":
    optimizer = PromptOptimizer()
    
    # 创建价值因子分析提示词
    value_prompt = optimizer.create_optimized_prompt(
        "价值因子",
        "贵州茅台 白酒 10000 8000 1800 2年 人民币 A股",
        "风险承受能力：中等，投资期限：5-10年"
    )
    
    print("优化后的价值因子提示词:")
    print(value_prompt)