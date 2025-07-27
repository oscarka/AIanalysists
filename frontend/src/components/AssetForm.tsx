import React, { useState } from 'react';
import { Form, Input, InputNumber, Button, Space } from 'antd';

const AssetForm = ({ onFinish }: { onFinish: (values: any) => void }) => {
  const [form] = Form.useForm();
  
  // 使用useState来管理初始数据，避免重复渲染
  const [initialAssets] = useState([
    { name: '贵州茅台', type: '股票', value: 100000, cost: 1800, price: 1900, holding_period: '3年', currency: 'CNY', market: 'A股' },
    { name: '腾讯控股', type: '股票', value: 80000, cost: 350, price: 380, holding_period: '2年', currency: 'CNY', market: '港股' },
    { name: '苹果公司', type: '股票', value: 120000, cost: 150, price: 170, holding_period: '1年', currency: 'USD', market: '美股' },
    { name: '黄金ETF', type: '基金', value: 50000, cost: 3.8, price: 4.2, holding_period: '6个月', currency: 'CNY', market: 'A股' },
    { name: '国债ETF', type: '债券', value: 60000, cost: 100, price: 102, holding_period: '1年', currency: 'CNY', market: 'A股' }
  ]);

  const handleReset = () => {
    form.resetFields();
  };

  const handleLoadExample = () => {
    const exampleData = {
      client_profile: {
        risk_tolerance: '中等',
        investment_horizon: '5-10年',
        income_level: '中等',
        age_group: '30-50岁',
        investment_goal: '资产增值'
      },
      assets: [
        { name: '招商银行', type: '股票', value: 50000, cost: 35, price: 38, holding_period: '2年', currency: 'CNY', market: 'A股' },
        { name: '阿里巴巴', type: '股票', value: 80000, cost: 180, price: 200, holding_period: '1年', currency: 'HKD', market: '港股' },
        { name: '特斯拉', type: '股票', value: 120000, cost: 200, price: 220, holding_period: '6个月', currency: 'USD', market: '美股' },
        { name: '易方达消费行业', type: '基金', value: 30000, cost: 2.5, price: 2.8, holding_period: '1年', currency: 'CNY', market: '基金' },
        { name: '国债ETF', type: '债券', value: 60000, cost: 100, price: 102, holding_period: '1年', currency: 'CNY', market: 'A股' }
      ]
    };
    form.setFieldsValue(exampleData);
  };

  return (
    <Form form={form} name="asset-form" onFinish={onFinish} autoComplete="off" layout="vertical">
      <h3>客户信息</h3>
      <div style={{ marginBottom: '16px', padding: '12px', background: '#e6f7ff', borderRadius: '6px', border: '1px solid #91d5ff' }}>
        <p style={{ margin: 0, fontSize: '14px', color: '#1890ff' }}>
          💡 <strong>填写说明：</strong>以下为客户画像信息，系统将根据这些信息提供个性化投资建议
        </p>
      </div>
      <Form.Item name="client_profile" initialValue={{
        risk_tolerance: '中等',
        investment_horizon: '5-10年',
        income_level: '中等',
        age_group: '30-50岁',
        investment_goal: '资产增值'
      }}>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: '12px',
          padding: '12px',
          background: '#f5f5f5',
          borderRadius: '6px'
        }}>
          <div><strong>风险承受能力：</strong>中等</div>
          <div><strong>投资期限：</strong>5-10年</div>
          <div><strong>收入水平：</strong>中等</div>
          <div><strong>年龄组：</strong>30-50岁</div>
          <div><strong>投资目标：</strong>资产增值</div>
        </div>
      </Form.Item>
      
      <h3>资产明细</h3>
      <div style={{ marginBottom: '16px', padding: '12px', background: '#f6ffed', borderRadius: '6px', border: '1px solid #b7eb8f' }}>
        <p style={{ margin: 0, fontSize: '14px', color: '#52c41a' }}>
          📊 <strong>填写说明：</strong>请填写您的实际投资组合。系统预置了示例数据，您可以修改或添加自己的资产。
        </p>
        <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
          <strong>字段说明：</strong><br/>
          • <strong>市值</strong>：当前持有该资产的总价值（元）<br/>
          • <strong>买入成本</strong>：买入时的价格<br/>
          • <strong>现价</strong>：当前市场价格<br/>
          • <strong>类型</strong>：股票、基金、债券、ETF等<br/>
          • <strong>市场</strong>：A股、港股、美股、基金等
        </div>
      </div>
      <Form.List name="assets" initialValue={initialAssets}>
        {(fields, { add, remove }) => (
          <>
            {fields.map(({ key, name, ...restField }) => (
              <div key={key} style={{ 
                border: '1px solid #d9d9d9', 
                borderRadius: '8px', 
                padding: '16px', 
                marginBottom: '16px',
                background: '#fafafa'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <h4 style={{ margin: 0, color: '#1890ff' }}>资产 #{name + 1}</h4>
                  <Button onClick={() => remove(name)} danger size="small">删除</Button>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
                  <Form.Item {...restField} name={[name, 'name']} label="资产名称" rules={[{ required: true }]}>
                    <Input placeholder="如：贵州茅台" />
                  </Form.Item>
                  <Form.Item {...restField} name={[name, 'type']} label="类型" rules={[{ required: true }]}>
                    <Input placeholder="如：股票、基金、债券" />
                  </Form.Item>
                  <Form.Item {...restField} name={[name, 'value']} label="市值（元）" rules={[{ required: true }]}>
                    <InputNumber min={0} placeholder="如：100000" style={{ width: '100%' }} />
                  </Form.Item>
                  <Form.Item {...restField} name={[name, 'cost']} label="买入成本" rules={[{ required: true }]}>
                    <InputNumber min={0} placeholder="如：1800" style={{ width: '100%' }} />
                  </Form.Item>
                  <Form.Item {...restField} name={[name, 'price']} label="现价" rules={[{ required: true }]}>
                    <InputNumber min={0} placeholder="如：1900" style={{ width: '100%' }} />
                  </Form.Item>
                  <Form.Item {...restField} name={[name, 'holding_period']} label="持有周期">
                    <Input placeholder="如：3年、6个月" />
                  </Form.Item>
                  <Form.Item {...restField} name={[name, 'currency']} label="币种">
                    <Input placeholder="如：CNY、USD、HKD" />
                  </Form.Item>
                  <Form.Item {...restField} name={[name, 'market']} label="市场">
                    <Input placeholder="如：A股、港股、美股" />
                  </Form.Item>
                </div>
              </div>
            ))}
            <Form.Item>
              <Button type="dashed" onClick={() => add()} block> 添加资产 </Button>
            </Form.Item>
          </>
        )}
      </Form.List>
      <Form.Item>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <Button type="primary" htmlType="submit">提交分析</Button>
          <Button onClick={handleLoadExample}>加载示例数据</Button>
          <Button onClick={handleReset}>重置表单</Button>
        </div>
      </Form.Item>
    </Form>
  );
};

export default AssetForm;