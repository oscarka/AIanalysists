# FinRobotApp 智能体资产配置系统

## 目录结构

```
FinRobotApp/
├── backend/           # FastAPI后端
│   ├── main.py        # 主API服务
│   ├── requirements.txt
│   └── finrobot/      # 你的finrobot核心代码（可软链或复制）
├── frontend/          # React + Ant Design前端
│   ├── package.json
│   └── src/
│       ├── api.ts
│       ├── App.tsx
│       ├── index.tsx
│       ├── pages/
│       │   └── Home.tsx
│       └── components/
│           └── AssetForm.tsx
```

## 快速启动

### 后端（FastAPI）
```bash
cd backend
pip install -r requirements.txt
# 配置API Key等环境变量
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 前端（React）
```bash
cd frontend
npm install
npm start
```

### Railway/Vercel部署
- 后端：Railway新建Python服务，上传backend目录，配置API Key等环境变量
- 前端：Vercel/Netlify/或Railway静态服务，上传frontend目录
- 前端API地址建议用环境变量配置

## 环境变量说明
- `OAI_CONFIG_LIST`、`config_api_keys`：大模型和数据API密钥，需在Railway后台配置
- 详见backend/main.py注释

## 主要功能
- 多智能体资产配置分析（价值、成长、动量、质量、波动率、流动性、情绪、宏观）
- CIO全局配置建议
- 结构化输出，便于前端展示和报告导出
- 前端支持多资产录入、结果可视化

## 二次开发建议
- 新增/调整分析师提示词，只需改backend/main.py中的prompt
- 支持多用户、历史记录、导出等可扩展

---
如有问题可随时联系开发者！