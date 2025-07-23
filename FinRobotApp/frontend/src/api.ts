import axios from 'axios';

export async function analyzeAssets(data: any) {
  // Railway部署时建议用环境变量配置API地址
  return axios.post('/api/analyze', data).then(res => res.data);
}