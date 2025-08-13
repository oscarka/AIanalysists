import React, { useState } from 'react';
import { Card, Spin, message, Radio, Space, Button } from 'antd';
import AssetForm from '../components/AssetForm';
import { analyzeAssets } from '../api';

const Home = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [cacheChoice, setCacheChoice] = useState<'restart' | 'continue' | 'view_history'>('restart');

  const onFinish = async (values: any) => {
    setLoading(true);
    setResult(null);
    try {
      // 确保数据格式正确
      const requestData = {
        assets: values.assets || [],
        client_profile: values.client_profile || {},
        user_choice: cacheChoice
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
      <div style={{ marginBottom: 24, padding: '16px', background: '#f5f5f5', borderRadius: '6px' }}>
        <h4 style={{ marginBottom: 16 }}>🔄 分析模式选择</h4>
        <Radio.Group value={cacheChoice} onChange={(e) => setCacheChoice(e.target.value)}>
          <Space direction="vertical">
            <Radio value="restart">
              <strong>🆕 重新开始分析</strong>
              <div style={{ fontSize: '12px', color: '#666', marginLeft: 24 }}>
                清除所有缓存，从头开始新的分析
              </div>
            </Radio>
            <Radio value="continue">
              <strong>▶️ 继续之前分析</strong>
              <div style={{ fontSize: '12px', color: '#666', marginLeft: 24 }}>
                基于之前的分析结果继续深入
              </div>
            </Radio>
            <Radio value="view_history">
              <strong>📋 查看历史记录</strong>
              <div style={{ fontSize: '12px', color: '#666', marginLeft: 24 }}>
                查看之前的分析记录和结果
              </div>
            </Radio>
          </Space>
        </Radio.Group>
        <div style={{ marginTop: 16, fontSize: '12px', color: '#666' }}>
          💡 提示：首次使用建议选择"重新开始分析"
        </div>
      </div>
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