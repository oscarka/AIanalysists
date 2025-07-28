# Manus学习优化系统
# 基于Manus方法的agent学习和优化

import json
import time
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
import numpy as np

@dataclass
class LearningExample:
    """学习样本"""
    input_data: Dict[str, Any]
    expected_output: str
    actual_output: str
    quality_score: float
    timestamp: float
    agent_name: str
    prompt_version: str

class ManusLearningSystem:
    """Manus学习系统"""
    
    def __init__(self):
        self.learning_examples = []
        self.agent_performance = defaultdict(list)
        self.prompt_versions = {}
        self.adaptation_rules = []
        
    def add_example(self, example: LearningExample):
        """添加学习样本"""
        self.learning_examples.append(example)
        self.agent_performance[example.agent_name].append({
            'quality': example.quality_score,
            'timestamp': example.timestamp,
            'prompt_version': example.prompt_version
        })
    
    def analyze_agent_performance(self, agent_name: str) -> Dict[str, Any]:
        """分析agent性能"""
        if agent_name not in self.agent_performance:
            return {}
        
        performances = self.agent_performance[agent_name]
        if not performances:
            return {}
        
        quality_scores = [p['quality'] for p in performances]
        recent_performances = [p for p in performances if time.time() - p['timestamp'] < 86400]  # 最近24小时
        
        return {
            'avg_quality': np.mean(quality_scores),
            'quality_trend': self._calculate_trend(quality_scores),
            'recent_avg_quality': np.mean([p['quality'] for p in recent_performances]) if recent_performances else 0,
            'total_examples': len(performances),
            'best_prompt_version': self._find_best_prompt_version(agent_name)
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """计算趋势"""
        if len(values) < 2:
            return "stable"
        
        # 简单线性回归
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        if slope > 0.01:
            return "improving"
        elif slope < -0.01:
            return "declining"
        else:
            return "stable"
    
    def _find_best_prompt_version(self, agent_name: str) -> str:
        """找到最佳提示词版本"""
        performances = self.agent_performance[agent_name]
        if not performances:
            return "default"
        
        # 按提示词版本分组计算平均质量
        version_quality = defaultdict(list)
        for p in performances:
            version_quality[p['prompt_version']].append(p['quality'])
        
        best_version = max(version_quality.items(), key=lambda x: np.mean(x[1]))[0]
        return best_version

class AdaptivePromptGenerator:
    """自适应提示词生成器"""
    
    def __init__(self, learning_system: ManusLearningSystem):
        self.learning_system = learning_system
        self.prompt_templates = {}
        self.adaptation_history = []
    
    def generate_adaptive_prompt(self, agent_name: str, base_prompt: str, 
                               context: Dict[str, Any]) -> str:
        """生成自适应提示词"""
        # 分析历史性能
        performance = self.learning_system.analyze_agent_performance(agent_name)
        
        # 根据性能调整提示词
        adapted_prompt = self._adapt_prompt(base_prompt, performance, context)
        
        # 记录适配历史
        self.adaptation_history.append({
            'agent_name': agent_name,
            'original_prompt': base_prompt,
            'adapted_prompt': adapted_prompt,
            'performance': performance,
            'timestamp': time.time()
        })
        
        return adapted_prompt
    
    def _adapt_prompt(self, base_prompt: str, performance: Dict[str, Any], 
                     context: Dict[str, Any]) -> str:
        """根据性能调整提示词"""
        adapted_prompt = base_prompt
        
        # 如果质量较低，增加更具体的指导
        if performance.get('avg_quality', 0) < 0.7:
            adapted_prompt += "\n\n特别注意：请确保分析逻辑清晰，数据来源可靠，建议具体可操作。"
        
        # 如果质量在下降，简化提示词
        if performance.get('quality_trend') == 'declining':
            adapted_prompt = self._simplify_prompt(adapted_prompt)
        
        # 根据上下文调整
        if context.get('asset_type') == 'high_risk':
            adapted_prompt += "\n\n风险提示：请特别关注高风险资产的风险因素。"
        elif context.get('asset_type') == 'conservative':
            adapted_prompt += "\n\n保守策略：请重点关注资产的安全性和稳定性。"
        
        return adapted_prompt
    
    def _simplify_prompt(self, prompt: str) -> str:
        """简化提示词"""
        # 移除冗余内容，保留核心要求
        lines = prompt.split('\n')
        simplified_lines = []
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['专业分析', '通俗解释', '可操作建议', '风险提示']):
                simplified_lines.append(line)
            elif line.strip() and not line.startswith('注意'):
                simplified_lines.append(line)
        
        return '\n'.join(simplified_lines)

class QualityEvaluator:
    """质量评估器"""
    
    def __init__(self):
        self.evaluation_criteria = {
            'completeness': 0.3,  # 完整性
            'accuracy': 0.3,      # 准确性
            'actionability': 0.2,  # 可操作性
            'clarity': 0.2        # 清晰度
        }
    
    def evaluate_response(self, response: str, expected_sections: List[str]) -> float:
        """评估响应质量"""
        scores = {}
        
        # 完整性评估
        scores['completeness'] = self._evaluate_completeness(response, expected_sections)
        
        # 准确性评估（基于关键词和逻辑）
        scores['accuracy'] = self._evaluate_accuracy(response)
        
        # 可操作性评估
        scores['actionability'] = self._evaluate_actionability(response)
        
        # 清晰度评估
        scores['clarity'] = self._evaluate_clarity(response)
        
        # 计算加权总分
        total_score = sum(scores[key] * self.evaluation_criteria[key] 
                         for key in scores)
        
        return total_score
    
    def _evaluate_completeness(self, response: str, expected_sections: List[str]) -> float:
        """评估完整性"""
        found_sections = 0
        for section in expected_sections:
            if section in response:
                found_sections += 1
        
        return found_sections / len(expected_sections) if expected_sections else 0
    
    def _evaluate_accuracy(self, response: str) -> float:
        """评估准确性"""
        accuracy_indicators = [
            '基于', '数据显示', '历史', '对比', '分析', '评估'
        ]
        
        score = 0
        for indicator in accuracy_indicators:
            if indicator in response:
                score += 0.2
        
        return min(score, 1.0)
    
    def _evaluate_actionability(self, response: str) -> float:
        """评估可操作性"""
        action_indicators = [
            '建议', '可以', '考虑', '关注', '增持', '减持', '持有'
        ]
        
        score = 0
        for indicator in action_indicators:
            if indicator in response:
                score += 0.15
        
        return min(score, 1.0)
    
    def _evaluate_clarity(self, response: str) -> float:
        """评估清晰度"""
        # 检查句子长度、段落结构等
        sentences = response.split('。')
        avg_sentence_length = np.mean([len(s) for s in sentences if s.strip()])
        
        # 理想的句子长度在20-50字之间
        if 20 <= avg_sentence_length <= 50:
            return 1.0
        elif 10 <= avg_sentence_length <= 80:
            return 0.7
        else:
            return 0.4

class ContinuousLearningAgent:
    """持续学习Agent"""
    
    def __init__(self, agent_name: str, base_prompt: str):
        self.agent_name = agent_name
        self.base_prompt = base_prompt
        self.learning_system = ManusLearningSystem()
        self.prompt_generator = AdaptivePromptGenerator(self.learning_system)
        self.quality_evaluator = QualityEvaluator()
        self.version_counter = 0
    
    def generate_response(self, input_data: Dict[str, Any], 
                         expected_sections: List[str]) -> str:
        """生成响应"""
        # 生成自适应提示词
        adapted_prompt = self.prompt_generator.generate_adaptive_prompt(
            self.agent_name, self.base_prompt, input_data
        )
        
        # 这里应该调用实际的LLM API
        # 为了演示，我们返回一个模拟响应
        response = self._simulate_llm_response(adapted_prompt, input_data)
        
        # 评估响应质量
        quality_score = self.quality_evaluator.evaluate_response(response, expected_sections)
        
        # 记录学习样本
        example = LearningExample(
            input_data=input_data,
            expected_output="",  # 这里应该有期望输出
            actual_output=response,
            quality_score=quality_score,
            timestamp=time.time(),
            agent_name=self.agent_name,
            prompt_version=f"v{self.version_counter}"
        )
        
        self.learning_system.add_example(example)
        
        return response
    
    def _simulate_llm_response(self, prompt: str, input_data: Dict[str, Any]) -> str:
        """模拟LLM响应"""
        # 这里应该调用实际的LLM API
        # 返回模拟响应用于演示
        return f"基于{prompt[:50]}...的分析结果"
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """获取学习洞察"""
        performance = self.learning_system.analyze_agent_performance(self.agent_name)
        
        insights = {
            'performance_summary': performance,
            'learning_suggestions': self._generate_learning_suggestions(performance),
            'prompt_optimization': self._suggest_prompt_optimization(performance)
        }
        
        return insights
    
    def _generate_learning_suggestions(self, performance: Dict[str, Any]) -> List[str]:
        """生成学习建议"""
        suggestions = []
        
        if performance.get('avg_quality', 0) < 0.7:
            suggestions.append("增加更多专业背景信息到提示词中")
            suggestions.append("提供更具体的输出格式要求")
        
        if performance.get('quality_trend') == 'declining':
            suggestions.append("简化提示词，减少复杂性")
            suggestions.append("增加更多示例到提示词中")
        
        if performance.get('total_examples', 0) < 10:
            suggestions.append("需要更多样本数据来训练模型")
        
        return suggestions
    
    def _suggest_prompt_optimization(self, performance: Dict[str, Any]) -> Dict[str, Any]:
        """建议提示词优化"""
        return {
            'current_quality': performance.get('avg_quality', 0),
            'target_quality': 0.8,
            'suggested_improvements': [
                "增加专业术语定义",
                "提供更多分析框架",
                "明确输出格式要求"
            ]
        }

# 使用示例
if __name__ == "__main__":
    # 创建持续学习agent
    value_agent = ContinuousLearningAgent(
        "Value_Factor_Analyst",
        "你是价值因子分析师，请分析资产估值..."
    )
    
    # 模拟多次交互
    for i in range(5):
        response = value_agent.generate_response(
            {'assets': ['茅台', '腾讯'], 'risk_level': 'medium'},
            ['专业分析', '通俗解释', '可操作建议', '风险提示']
        )
        
        print(f"第{i+1}次响应: {response[:100]}...")
    
    # 获取学习洞察
    insights = value_agent.get_learning_insights()
    print("学习洞察:", json.dumps(insights, indent=2, ensure_ascii=False))