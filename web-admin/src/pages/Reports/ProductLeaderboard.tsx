/**
 * Product Leaderboard Page
 * 
 * 商品排行榜页：展示商品销量、收入、利润排行
 */

import React, { useState, useEffect } from 'react';
import { Card, Table, Select, Radio, message, Tag } from 'antd';
import { TrophyOutlined, CrownOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { getProductLeaderboard, ProductLeaderboardItem } from '../../services/report';
import { getEvents, Event } from '../../services/event';

const { Option } = Select;

const ProductLeaderboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [products, setProducts] = useState<ProductLeaderboardItem[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<number | undefined>(undefined);
  const [metric, setMetric] = useState<'sales' | 'revenue' | 'profit'>('sales');
  const [limit, setLimit] = useState(10);

  useEffect(() => {
    loadEvents();
  }, []);

  useEffect(() => {
    loadLeaderboard();
  }, [selectedEventId, metric, limit]);

  const loadEvents = async () => {
    try {
      const data = await getEvents();
      setEvents(data.events);
    } catch (error) {
      console.error('Failed to load events:', error);
    }
  };

  const loadLeaderboard = async () => {
    setLoading(true);
    try {
      const data = await getProductLeaderboard(metric, selectedEventId, limit);
      setProducts(data.leaderboard);
    } catch (error) {
      console.error('Failed to load leaderboard:', error);
      message.error('加载排行榜失败');
    } finally {
      setLoading(false);
    }
  };

  const getRankIcon = (rank: number) => {
    if (rank === 1) return <CrownOutlined style={{ color: '#FFD700', fontSize: '20px' }} />;
    if (rank === 2) return <TrophyOutlined style={{ color: '#C0C0C0', fontSize: '18px' }} />;
    if (rank === 3) return <TrophyOutlined style={{ color: '#CD7F32', fontSize: '16px' }} />;
    return <span style={{ fontWeight: 'bold' }}>{rank}</span>;
  };

  const columns: ColumnsType<ProductLeaderboardItem> = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 80,
      align: 'center',
      render: (rank: number) => getRankIcon(rank),
    },
    {
      title: '商品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      width: 200,
      render: (text: string, record) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{text}</div>
          <div style={{ fontSize: '12px', color: '#8c8c8c' }}>
            ID: {record.product_id}
          </div>
        </div>
      ),
    },
    {
      title: '所属摊位',
      dataIndex: 'booth_name',
      key: 'booth_name',
      width: 200,
      render: (text: string, record) => (
        <div>
          <div>{text}</div>
          <div style={{ fontSize: '12px', color: '#8c8c8c' }}>
            ID: {record.booth_id}
          </div>
        </div>
      ),
    },
    {
      title: '指标值',
      dataIndex: 'value',
      key: 'value',
      width: 150,
      align: 'right',
      render: (value: number) => {
        let display = '';
        let color = '#1890ff';
        
        if (metric === 'sales') {
          display = `${value} 件`;
        } else if (metric === 'revenue' || metric === 'profit') {
          display = `¥${value.toFixed(2)}`;
          color = value >= 0 ? '#3f8600' : '#cf1322';
        }
        
        return (
          <Tag color={color} style={{ fontSize: '14px', fontWeight: 'bold' }}>
            {display}
          </Tag>
        );
      },
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: '16px' }}>
          <h2>商品排行榜 🏆</h2>
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
            <span style={{ marginRight: '8px' }}>排序指标：</span>
            <Radio.Group value={metric} onChange={(e) => setMetric(e.target.value)}>
              <Radio.Button value="sales">销量</Radio.Button>
              <Radio.Button value="revenue">收入</Radio.Button>
              <Radio.Button value="profit">利润</Radio.Button>
            </Radio.Group>
          </div>

          <div>
            <span style={{ marginRight: '8px' }}>显示数量：</span>
            <Select value={limit} onChange={setLimit} style={{ width: 100 }}>
              <Option value={10}>TOP 10</Option>
              <Option value={20}>TOP 20</Option>
              <Option value={50}>TOP 50</Option>
            </Select>
          </div>
        </div>

        <Table
          columns={columns}
          dataSource={products}
          rowKey="product_id"
          loading={loading}
          pagination={false}
          rowClassName={(record) => {
            if (record.rank === 1) return 'rank-1';
            if (record.rank === 2) return 'rank-2';
            if (record.rank === 3) return 'rank-3';
            return '';
          }}
        />
      </Card>

      <style>{`
        .rank-1 {
          background-color: #fffbe6 !important;
        }
        .rank-2 {
          background-color: #f0f5ff !important;
        }
        .rank-3 {
          background-color: #fff7e6 !important;
        }
      `}</style>
    </div>
  );
};

export default ProductLeaderboard;
