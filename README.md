# FinRobot 智能体资产配置系统

一个基于AI智能体的资产配置分析系统，提供多因子分析和个性化投资建议。

## 项目结构

```
FinRobotApp/
├── backend/          # FastAPI后端服务
│   ├── main.py      # 主服务文件
│   ├── finrobot/    # 智能体核心模块
│   └── start_backend.py  # 后端启动脚本
└── frontend/        # React前端应用
    ├── src/         # 源代码
    └── package.json # 前端依赖
```

## 快速启动

### 1. 配置API密钥

#### 后端配置

编辑 `backend/config_api_keys` 文件：
```json
{
    "openai_api_key": "你的OpenAI API密钥",
    "finnhub_api_key": "你的Finnhub API密钥", 
    "sec_api_key": "你的SEC API密钥"
}
```

编辑 `backend/OAI_CONFIG_LIST` 文件：
```json
[
    {
        "model": "deepseek-chat",
        "api_key": "你的API密钥",
        "base_url": "https://api.deepseek.com/v1"
    }
]
```

### 2. 启动后端

```bash
cd backend
python start_backend.py
```

或者手动启动：
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 启动前端

```bash
cd frontend
npm install
npm start
```

## 功能特性

### 多因子分析
- **价值因子**：PE、PB、股息率等估值指标分析
- **成长因子**：营收、净利润、现金流增长分析
- **动量因子**：价格趋势、资金流向分析
- **质量因子**：ROE、ROA、财务健康度分析
- **波动率因子**：风险水平、夏普比率分析
- **流动性因子**：成交量、流动性风险分析
- **情绪因子**：市场情绪、热点板块分析
- **宏观因子**：利率、汇率、政策环境影响分析

### 智能建议
- 基于客户风险偏好的个性化配置
- 多种投资策略方案（稳健型、平衡型、进取型）
- 动态调整建议和风险提示
- 后续跟踪和复盘建议

## 默认数据示例

系统预置了以下示例资产组合：

1. **贵州茅台** - A股白酒龙头
2. **腾讯控股** - 港股科技巨头
3. **苹果公司** - 美股科技股
4. **黄金ETF** - 避险资产
5. **国债ETF** - 固定收益资产

客户信息：
- 风险承受能力：中等
- 投资期限：5-10年
- 收入水平：中等
- 年龄组：30-50岁
- 投资目标：资产增值

## API接口

### 资产分析接口
- **URL**: `POST /analyze`
- **功能**: 多因子资产配置分析
- **参数**: 
  - `assets`: 资产列表
  - `client_profile`: 客户信息

## 技术栈

### 后端
- FastAPI - Web框架
- AutoGen - 智能体框架
- Pandas - 数据处理
- OpenAI/DeepSeek - AI模型

### 前端
- React 18 - 前端框架
- Ant Design - UI组件库
- TypeScript - 类型安全
- Axios - HTTP客户端

## 开发说明

### 添加新的分析因子
1. 在 `backend/main.py` 的 `factor_prompts` 中添加新的因子分析器
2. 定义分析器的专业角色和提示词
3. 系统会自动集成到分析流程中

### 自定义客户画像
前端支持自定义客户信息，包括：
- 风险承受能力
- 投资期限
- 收入水平
- 年龄组
- 投资目标

## 注意事项

1. **API密钥安全**：请妥善保管API密钥，不要提交到版本控制系统
2. **网络连接**：确保能够访问OpenAI/DeepSeek等AI服务
3. **数据准确性**：系统分析基于输入数据，请确保数据准确性
4. **投资风险**：AI建议仅供参考，投资有风险，决策需谨慎

## 故障排除

### 前端代理错误
如果看到 "Proxy error: Could not proxy request"，说明后端服务未启动，请先启动后端服务。

### API密钥错误
如果分析失败，请检查API密钥配置是否正确。

### 依赖安装问题
如果遇到依赖安装问题，请确保Python版本 >= 3.8，Node.js版本 >= 14。