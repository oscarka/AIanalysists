# 多API密钥配置示例
# 用于提升多agent系统的并发性能

import json
import asyncio
from typing import List, Dict, Any
import aiohttp
import time

# 多个API密钥配置
MULTI_API_CONFIG = [
    {
        "model": "deepseek-chat",
        "api_key": "your-deepseek-api-key-1",
        "base_url": "https://api.deepseek.com/v1",
        "weight": 1.0  # 权重，用于负载均衡
    },
    {
        "model": "deepseek-chat", 
        "api_key": "your-deepseek-api-key-2",
        "base_url": "https://api.deepseek.com/v1",
        "weight": 1.0
    },
    {
        "model": "deepseek-chat",
        "api_key": "your-deepseek-api-key-3", 
        "base_url": "https://api.deepseek.com/v1",
        "weight": 1.0
    }
]

# 负载均衡配置
class LoadBalancer:
    def __init__(self, configs: List[Dict[str, Any]]):
        self.configs = configs
        self.current_index = 0
        self.request_counts = [0] * len(configs)
    
    def get_next_config(self) -> Dict[str, Any]:
        """轮询方式获取下一个配置"""
        config = self.configs[self.current_index]
        self.request_counts[self.current_index] += 1
        self.current_index = (self.current_index + 1) % len(self.configs)
        return config
    
    def get_least_loaded_config(self) -> Dict[str, Any]:
        """获取负载最轻的配置"""
        min_count = min(self.request_counts)
        min_indices = [i for i, count in enumerate(self.request_counts) if count == min_count]
        selected_index = min_indices[0]
        self.request_counts[selected_index] += 1
        return self.configs[selected_index]

# 异步并发处理
async def process_agents_concurrently(agent_configs: List[Dict], message: str):
    """并发处理多个agent"""
    load_balancer = LoadBalancer(MULTI_API_CONFIG)
    
    async def process_single_agent(agent_config: Dict):
        api_config = load_balancer.get_least_loaded_config()
        # 这里集成你的agent处理逻辑
        return await process_agent_with_config(agent_config, api_config, message)
    
    # 并发执行所有agent
    tasks = [process_single_agent(config) for config in agent_configs]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return results

async def process_agent_with_config(agent_config: Dict, api_config: Dict, message: str):
    """使用指定API配置处理单个agent"""
    # 这里实现具体的agent处理逻辑
    # 集成到你的SingleAssistant类中
    pass

# 性能监控
class PerformanceMonitor:
    def __init__(self):
        self.response_times = []
        self.error_counts = {}
        self.success_counts = {}
    
    def record_response_time(self, agent_name: str, response_time: float):
        self.response_times.append((agent_name, response_time))
    
    def record_error(self, agent_name: str):
        self.error_counts[agent_name] = self.error_counts.get(agent_name, 0) + 1
    
    def record_success(self, agent_name: str):
        self.success_counts[agent_name] = self.success_counts.get(agent_name, 0) + 1
    
    def get_stats(self):
        return {
            "avg_response_time": sum(t[1] for t in self.response_times) / len(self.response_times) if self.response_times else 0,
            "total_requests": len(self.response_times),
            "error_counts": self.error_counts,
            "success_counts": self.success_counts
        }

# 使用示例
if __name__ == "__main__":
    # 示例agent配置
    agent_configs = [
        {"name": "Value_Factor_Analyst", "profile": "价值因子分析..."},
        {"name": "Growth_Factor_Analyst", "profile": "成长因子分析..."},
        {"name": "Momentum_Factor_Analyst", "profile": "动量因子分析..."},
        # ... 更多agent
    ]
    
    # 并发处理
    async def main():
        start_time = time.time()
        results = await process_agents_concurrently(agent_configs, "分析请求")
        end_time = time.time()
        
        print(f"总耗时: {end_time - start_time:.2f}秒")
        print(f"处理了 {len(results)} 个agent")
        
        # 性能统计
        monitor = PerformanceMonitor()
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                monitor.record_error(agent_configs[i]["name"])
            else:
                monitor.record_success(agent_configs[i]["name"])
        
        print("性能统计:", monitor.get_stats())
    
    # asyncio.run(main())