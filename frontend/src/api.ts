import axios from 'axios';

export async function analyzeAssets(data: any) {
  // 直接使用后端URL，避免代理问题
  return axios.post('http://localhost:8000/analyze', data).then(res => res.data);
}