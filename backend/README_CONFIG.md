# FinRobot 配置说明

## 🚀 快速配置

### 1. 配置 API 密钥

编辑 `config_api_keys` 文件：
```json
{
    "openai_api_key": "您的OpenAI API密钥",
    "finnhub_api_key": "您的Finnhub API密钥", 
    "sec_api_key": "您的SEC API密钥"
}
```

### 2. 配置 AI 模型

编辑 `OAI_CONFIG_LIST` 文件：
```json
[
    {
        "model": "deepseek-chat",
        "api_key": "您的DeepSeek API密钥",
        "base_url": "https://api.deepseek.com/v1"
    }
]
```

## 🔑 如何获取 API 密钥

- **OpenAI**: https://platform.openai.com/api-keys
- **Finnhub**: https://finnhub.io/register  
- **SEC API**: https://sec-api.io/
- **DeepSeek**: https://platform.deepseek.com/

## ⚙️ 输出长度优化

系统已优化输出长度：
- 各因子分析：控制在 150 字以内
- CIO 汇总：控制在 300 字以内
- 使用简洁明了的语言表达核心观点

## 🧪 测试

配置完成后，访问：
- 后端健康检查：http://localhost:8000/health
- 前端应用：http://localhost:3000
