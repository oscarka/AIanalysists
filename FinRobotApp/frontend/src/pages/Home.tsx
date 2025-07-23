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
      const res = await analyzeAssets(values);
      setResult(res.result);
    } catch (e: any) {
      message.error(e.message || '分析失败');
    }
    setLoading(false);
  };

  return (
    <Card title="智能体资产配置分析" style={{ maxWidth: 900, margin: '40px auto' }}>
      <AssetForm onFinish={onFinish} />
      {loading && <Spin />}
      {result && (
        <div style={{ marginTop: 32 }}>
          <h3>全局配置建议（CIO）</h3>
          <pre style={{ background: '#f6f6f6', padding: 16 }}>{result.cio_result}</pre>
          <h3>各因子分析师建议</h3>
          <pre style={{ background: '#f6f6f6', padding: 16 }}>{JSON.stringify(result.factor_results, null, 2)}</pre>
        </div>
      )}
    </Card>
  );
};

export default Home;