/**
 * Booth Report Page
 * 
 * 摊位报表页：展示摊位维度的经营数据
 */

import React, { useState, useEffect } from 'react';
import { Table, Select, Button, message, Card, Tag } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { getBoothReport, exportReportExcel, downloadExcel, BoothReportItem } from '../../services/report';
import { getEvents, Event } from '../../services/event';

const { Option } = Select;

const BoothReport: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [booths, setBooths] = useState<BoothReportItem[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<number | undefined>(undefined);

  useEffect(() => {
    loadEvents();
  }, []);

  useEffect(() => {
    loadBoothReport();
  }, [selectedEventId]);

  const loadEvents = async () => {
    try {
      const data = await getEvents();
      setEvents(data.events);
    } catch (error) {
      console.error('Failed to load events:', error);
    }
  };

  const loadBoothReport = async () => {
    setLoading(true);
    try {
      const data = await getBoothReport(selectedEventId);
      setBooths(data.booths);
    } catch (error) {
      console.error('Failed to load booth report:', error);
      message.error('加载摊位报表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const blob = await exportReportExcel('booths', selectedEventId);
      const filename = `摊位报表_${selectedEventId || '全部'}_${new Date().toISOString().split('T')[0]}.xlsx`;
      downloadExcel(blob, filename);
      message.success('导出成功');
    } catch (error) {
      console.error('Failed to export:', error);
      message.error('导出失败');
    } finally {
      setExporting(false);
    }
  };

  const columns: ColumnsType<BoothReportItem> = [
    {
      title: '摊位ID',
      dataIndex: 'booth_id',
      key: 'booth_id',
      width: 80,
      fixed: 'left',
    },
    {
      title: '摊位名称',
      dataIndex: 'booth_name',
      key: 'booth_name',
      width: 150,
      fixed: 'left',
    },
    {
      title: '班级名称',
      dataIndex: 'class_name',
      key: 'class_name',
      width: 150,
    },
    {
      title: '营业额（元）',
      dataIndex: 'revenue',
      key: 'revenue',
      width: 120,
      align: 'right',
      render: (value: number) => `¥${value.toFixed(2)}`,
      sorter: (a, b) => a.revenue - b.revenue,
    },
    {
      title: '退款额（元）',
      dataIndex: 'refund_amount',
      key: 'refund_amount',
      width: 120,
      align: 'right',
      render: (value: number) => `¥${value.toFixed(2)}`,
      sorter: (a, b) => a.refund_amount - b.refund_amount,
    },
    {
      title: '净收入（元）',
      dataIndex: 'net_revenue',
      key: 'net_revenue',
      width: 120,
      align: 'right',
      render: (value: number) => (
        <span style={{ color: value >= 0 ? '#3f8600' : '#cf1322', fontWeight: 'bold' }}>
          ¥{value.toFixed(2)}
        </span>
      ),
      sorter: (a, b) => a.net_revenue - b.net_revenue,
    },
    {
      title: '销量（笔）',
      dataIndex: 'sales_count',
      key: 'sales_count',
      width: 100,
      align: 'right',
      sorter: (a, b) => a.sales_count - b.sales_count,
    },
    {
      title: '总成本（元）',
      dataIndex: 'total_cost',
      key: 'total_cost',
      width: 120,
      align: 'right',
      render: (value: number) => `¥${value.toFixed(2)}`,
      sorter: (a, b) => a.total_cost - b.total_cost,
    },
    {
      title: '利润（元）',
      dataIndex: 'profit',
      key: 'profit',
      width: 120,
      align: 'right',
      render: (value: number) => (
        <span style={{ color: value >= 0 ? '#3f8600' : '#cf1322', fontWeight: 'bold' }}>
          ¥{value.toFixed(2)}
        </span>
      ),
      sorter: (a, b) => a.profit - b.profit,
    },
    {
      title: '利润率（%）',
      dataIndex: 'profit_margin',
      key: 'profit_margin',
      width: 120,
      align: 'right',
      render: (value: number | null) => {
        if (value === null) return '-';
        const color = value >= 50 ? '#3f8600' : value >= 30 ? '#1890ff' : value >= 0 ? '#faad14' : '#cf1322';
        return <Tag color={color}>{value.toFixed(2)}%</Tag>;
      },
      sorter: (a, b) => (a.profit_margin || 0) - (b.profit_margin || 0),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>摊位报表</h2>
          <div>
            <Select
              placeholder="选择活动"
              style={{ width: 200, marginRight: '16px' }}
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
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              onClick={handleExport}
              loading={exporting}
            >
              导出 Excel
            </Button>
          </div>
        </div>

        <Table
          columns={columns}
          dataSource={booths}
          rowKey="booth_id"
          loading={loading}
          scroll={{ x: 1200 }}
          pagination={{
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 个摊位`,
          }}
        />
      </Card>
    </div>
  );
};

export default BoothReport;
