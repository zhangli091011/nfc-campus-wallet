/**
 * Export Page
 * 
 * 导出页：提供各类报表的 Excel 导出功能
 */

import React, { useState, useEffect } from 'react';
import { Card, Button, Select, Form, message, Divider, List } from 'antd';
import { DownloadOutlined, FileExcelOutlined } from '@ant-design/icons';
import { exportReportExcel, downloadExcel } from '../../services/report';
import { getEvents, Event } from '../../services/event';

const { Option } = Select;

interface ExportItem {
  key: string;
  title: string;
  description: string;
  reportType: 'summary' | 'booths' | 'products' | 'transactions';
}

const exportItems: ExportItem[] = [
  {
    key: 'summary',
    title: '总览统计报表',
    description: '包含总发放额度、总充值额、总消费额、总退款额、净消费额、总交易笔数、参与者数量、摊位数量',
    reportType: 'summary',
  },
  {
    key: 'booths',
    title: '摊位报表',
    description: '包含摊位营业额、退款额、净收入、销量、成本、利润、利润率等详细数据',
    reportType: 'booths',
  },
  {
    key: 'products',
    title: '商品报表',
    description: '包含商品销量、收入、成本、利润、利润率等详细数据',
    reportType: 'products',
  },
  {
    key: 'transactions',
    title: '交易流水报表',
    description: '包含所有交易记录的详细信息（最多导出 10000 条）',
    reportType: 'transactions',
  },
];

const ExportPage: React.FC = () => {
  const [events, setEvents] = useState<Event[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<number | undefined>(undefined);
  const [exportingMap, setExportingMap] = useState<Record<string, boolean>>({});

  useEffect(() => {
    loadEvents();
  }, []);

  const loadEvents = async () => {
    try {
      const data = await getEvents();
      setEvents(data.events);
    } catch (error) {
      console.error('Failed to load events:', error);
    }
  };

  const handleExport = async (item: ExportItem) => {
    setExportingMap((prev) => ({ ...prev, [item.key]: true }));
    
    try {
      const blob = await exportReportExcel(item.reportType, selectedEventId);
      
      // 生成文件名
      const eventName = selectedEventId
        ? events.find((e) => e.id === selectedEventId)?.name || `活动${selectedEventId}`
        : '全部活动';
      const date = new Date().toISOString().split('T')[0];
      const filename = `${item.title}_${eventName}_${date}.xlsx`;
      
      downloadExcel(blob, filename);
      message.success(`${item.title}导出成功`);
    } catch (error) {
      console.error('Failed to export:', error);
      message.error(`${item.title}导出失败`);
    } finally {
      setExportingMap((prev) => ({ ...prev, [item.key]: false }));
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: '24px' }}>
          <h2>报表导出 📊</h2>
          <p style={{ color: '#8c8c8c' }}>
            选择活动和报表类型，导出为 Excel 文件
          </p>
        </div>

        <Form layout="vertical">
          <Form.Item label="选择活动（可选）">
            <Select
              placeholder="不选择则导出所有活动数据"
              style={{ width: 300 }}
              allowClear
              value={selectedEventId}
              onChange={setSelectedEventId}
            >
              {events.map((event) => (
                <Option key={event.id} value={event.id}>
                  {event.name}
                </Option>
              ))}
            </Select>
          </Form.Item>
        </Form>

        <Divider />

        <List
          itemLayout="horizontal"
          dataSource={exportItems}
          renderItem={(item) => (
            <List.Item
              actions={[
                <Button
                  type="primary"
                  icon={<DownloadOutlined />}
                  loading={exportingMap[item.key]}
                  onClick={() => handleExport(item)}
                >
                  导出 Excel
                </Button>,
              ]}
            >
              <List.Item.Meta
                avatar={<FileExcelOutlined style={{ fontSize: '32px', color: '#52c41a' }} />}
                title={<span style={{ fontSize: '16px', fontWeight: 'bold' }}>{item.title}</span>}
                description={item.description}
              />
            </List.Item>
          )}
        />

        <Divider />

        <div style={{ marginTop: '24px', padding: '16px', backgroundColor: '#f0f2f5', borderRadius: '4px' }}>
          <h4>📝 导出说明</h4>
          <ul style={{ marginBottom: 0 }}>
            <li>所有金额单位为"元"，保留两位小数</li>
            <li>交易流水报表最多导出最近 10000 条记录</li>
            <li>导出的 Excel 文件包含完整的表头和数据</li>
            <li>如果不选择活动，将导出所有活动的数据</li>
            <li>建议使用 Microsoft Excel 或 WPS 表格打开</li>
          </ul>
        </div>
      </Card>
    </div>
  );
};

export default ExportPage;
