/**
 * Audit Logs Page
 * 
 * 异常审计日志页：展示高频退款、大额更正、可疑操作等异常记录
 */

import React, { useState, useEffect } from 'react';
import { Table, Select, Card, Tag, message, Space } from 'antd';
import { WarningOutlined, ExclamationCircleOutlined, AlertOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { getAuditLogs, AuditLogItem } from '../../services/report';
import { getEvents, Event } from '../../services/event';
import dayjs from 'dayjs';

const { Option } = Select;

const AuditLogs: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<number | undefined>(undefined);
  const [flagType, setFlagType] = useState('all');
  const [limit, setLimit] = useState(100);

  useEffect(() => {
    loadEvents();
  }, []);

  useEffect(() => {
    loadAuditLogs();
  }, [selectedEventId, flagType, limit]);

  const loadEvents = async () => {
    try {
      const data = await getEvents();
      setEvents(data.events);
    } catch (error) {
      console.error('Failed to load events:', error);
    }
  };

  const loadAuditLogs = async () => {
    setLoading(true);
    try {
      const data = await getAuditLogs(selectedEventId, flagType, limit);
      setLogs(data.logs);
    } catch (error) {
      console.error('Failed to load audit logs:', error);
      message.error('加载审计日志失败');
    } finally {
      setLoading(false);
    }
  };

  const getFlagIcon = (flagReason: string) => {
    if (flagReason.includes('高频退款')) {
      return <WarningOutlined style={{ color: '#faad14' }} />;
    }
    if (flagReason.includes('大额')) {
      return <ExclamationCircleOutlined style={{ color: '#cf1322' }} />;
    }
    if (flagReason.includes('可疑')) {
      return <AlertOutlined style={{ color: '#722ed1' }} />;
    }
    return null;
  };

  const getFlagColor = (flagReason: string) => {
    if (flagReason.includes('高频退款')) return 'warning';
    if (flagReason.includes('大额')) return 'error';
    if (flagReason.includes('可疑')) return 'purple';
    return 'default';
  };

  const getTransactionTypeTag = (type: string) => {
    const typeMap: Record<string, { text: string; color: string }> = {
      recharge: { text: '充值', color: 'blue' },
      pay: { text: '支付', color: 'green' },
      refund: { text: '退款', color: 'orange' },
      adjust: { text: '调整', color: 'purple' },
      issue: { text: '发卡', color: 'cyan' },
      void: { text: '作废', color: 'red' },
      expire: { text: '过期', color: 'default' },
    };
    
    const config = typeMap[type] || { text: type, color: 'default' };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  const columns: ColumnsType<AuditLogItem> = [
    {
      title: '交易ID',
      dataIndex: 'transaction_id',
      key: 'transaction_id',
      width: 100,
    },
    {
      title: '交易类型',
      dataIndex: 'transaction_type',
      key: 'transaction_type',
      width: 100,
      render: (type: string) => getTransactionTypeTag(type),
    },
    {
      title: '金额（元）',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      align: 'right',
      render: (value: number) => (
        <span style={{ fontWeight: 'bold' }}>¥{value.toFixed(2)}</span>
      ),
    },
    {
      title: '参与者',
      dataIndex: 'participant_name',
      key: 'participant_name',
      width: 120,
      render: (text: string | null) => text || '-',
    },
    {
      title: '摊位',
      dataIndex: 'booth_name',
      key: 'booth_name',
      width: 150,
      render: (text: string | null) => text || '-',
    },
    {
      title: '操作员',
      dataIndex: 'operator_username',
      key: 'operator_username',
      width: 120,
      render: (text: string | null) => text || '-',
    },
    {
      title: '异常标记',
      dataIndex: 'flag_reason',
      key: 'flag_reason',
      width: 200,
      render: (text: string) => (
        <Space>
          {getFlagIcon(text)}
          <Tag color={getFlagColor(text)}>{text}</Tag>
        </Space>
      ),
    },
    {
      title: '备注',
      dataIndex: 'remark',
      key: 'remark',
      width: 200,
      ellipsis: true,
      render: (text: string | null) => text || '-',
    },
    {
      title: '交易时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
      sorter: (a, b) => dayjs(a.created_at).unix() - dayjs(b.created_at).unix(),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: '16px' }}>
          <h2>异常审计日志 🔍</h2>
          <p style={{ color: '#8c8c8c' }}>
            监控高频退款、大额更正、可疑操作等异常交易记录
          </p>
        </div>

        <div style={{ marginBottom: '16px', display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
          <div>
            <span style={{ marginRight: '8px' }}>活动：</span>
            <Select
              placeholder="选择活动"
              style={{ width: 200 }}
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
          </div>

          <div>
            <span style={{ marginRight: '8px' }}>异常类型：</span>
            <Select value={flagType} onChange={setFlagType} style={{ width: 200 }}>
              <Option value="all">全部异常</Option>
              <Option value="high_frequency_refund">高频退款</Option>
              <Option value="large_adjustment">大额更正</Option>
              <Option value="suspicious_operation">可疑操作</Option>
            </Select>
          </div>

          <div>
            <span style={{ marginRight: '8px' }}>显示数量：</span>
            <Select value={limit} onChange={setLimit} style={{ width: 120 }}>
              <Option value={50}>最近 50 条</Option>
              <Option value={100}>最近 100 条</Option>
              <Option value={200}>最近 200 条</Option>
              <Option value={500}>最近 500 条</Option>
            </Select>
          </div>
        </div>

        <Table
          columns={columns}
          dataSource={logs}
          rowKey="transaction_id"
          loading={loading}
          scroll={{ x: 1400 }}
          pagination={{
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条异常记录`,
          }}
        />
      </Card>
    </div>
  );
};

export default AuditLogs;
