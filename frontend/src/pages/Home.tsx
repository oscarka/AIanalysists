import React, { useState } from 'react';
import { Card, Spin, message } from 'antd';
import AssetForm from '../components/AssetForm';
import { analyzeAssets } from '../api';

const Home = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const onFinish = async (values: any) => {
    setLoading(true);
    setResult(null);
    try {
      // 确保数据格式正确
      const requestData = {
        assets: values.assets || [],
        client_profile: values.client_profile || {}
      };
      
      console.log('发送的数据:', requestData);
      
      // 验证数据
      if (!requestData.assets || requestData.assets.length === 0) {
        message.error('请至少添加一个资产');
        setLoading(false);
        return;
      }
      
      const res = await analyzeAssets(requestData);
      console.log('收到的响应:', res);
      setResult(res);
    } catch (e: any) {
      console.error('请求错误:', e);
      message.error(e.response?.data?.detail || e.message || '分析失败');
    }
    setLoading(false);
  };

  return (
    <Card title="智能体资产配置分析" style={{ maxWidth: 900, margin: '40px auto' }}>
      <AssetForm onFinish={onFinish} />
      {loading && <Spin />}
      {result && (
        <div style={{ marginTop: 32 }}>
          {result.error && (
            <div style={{ background: '#fff2f0', border: '1px solid #ffccc7', padding: 16, marginBottom: 16 }}>
              <h3 style={{ color: '#cf1322' }}>⚠️ 配置提醒</h3>
              <p>{result.error}</p>
              <p style={{ fontSize: '12px', color: '#666' }}>如需真实AI分析，请配置有效的API密钥</p>
            </div>
          )}
          <h3>全局配置建议（CIO）</h3>
          <pre style={{ background: '#f6f6f6', padding: 16, whiteSpace: 'pre-wrap' }}>{result.cio_result}</pre>
          <h3>各因子分析师建议</h3>
          <div style={{ background: '#f6f6f6', padding: 16 }}>
            {Object.entries(result.factor_results).map(([name, content]) => (
              <div key={name} style={{ marginBottom: 16 }}>
                <h4 style={{ color: '#1890ff' }}>{name}</h4>
                <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{String(content)}</pre>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
};

export default Home;