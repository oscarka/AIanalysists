import React from 'react';
import { Form, Input, InputNumber, Button, Space } from 'antd';

const AssetForm = ({ onFinish }: { onFinish: (values: any) => void }) => {
  return (
    <Form name="asset-form" onFinish={onFinish} autoComplete="off" layout="vertical">
      <Form.List name="assets" initialValue={[
        { name: '贵州茅台', type: '股票', value: 100000, cost: 1800, price: 1900, holding_period: '3年', currency: 'CNY', market: 'A股' }
      ]}>
        {(fields, { add, remove }) => (
          <>
            {fields.map(({ key, name, ...restField }) => (
              <Space key={key} align="baseline">
                <Form.Item {...restField} name={[name, 'name']} label="资产名称" rules={[{ required: true }]}> <Input /> </Form.Item>
                <Form.Item {...restField} name={[name, 'type']} label="类型" rules={[{ required: true }]}> <Input /> </Form.Item>
                <Form.Item {...restField} name={[name, 'value']} label="市值" rules={[{ required: true }]}> <InputNumber min={0} /> </Form.Item>
                <Form.Item {...restField} name={[name, 'cost']} label="买入成本" rules={[{ required: true }]}> <InputNumber min={0} /> </Form.Item>
                <Form.Item {...restField} name={[name, 'price']} label="现价" rules={[{ required: true }]}> <InputNumber min={0} /> </Form.Item>
                <Form.Item {...restField} name={[name, 'holding_period']} label="持有周期"> <Input /> </Form.Item>
                <Form.Item {...restField} name={[name, 'currency']} label="币种"> <Input /> </Form.Item>
                <Form.Item {...restField} name={[name, 'market']} label="市场"> <Input /> </Form.Item>
                <Button onClick={() => remove(name)} danger>删除</Button>
              </Space>
            ))}
            <Form.Item>
              <Button type="dashed" onClick={() => add()} block> 添加资产 </Button>
            </Form.Item>
          </>
        )}
      </Form.List>
      <Form.Item>
        <Button type="primary" htmlType="submit">提交分析</Button>
      </Form.Item>
    </Form>
  );
};

export default AssetForm;