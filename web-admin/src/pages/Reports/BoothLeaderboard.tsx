/**
 * Booth Leaderboard Page
 * 
 * 摊位排行榜页：展示摊位营业额、利润、利润率排行
 */

import React, { useState, useEffect } from 'react';
import { Card, Table, Select, Radio, message, Tag } from 'antd';
import { TrophyOutlined, CrownOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import {
  getRevenueLeaderboard,
  getProfitLeaderboard,
  getRoiLeaderboard,
  LeaderboardItem,
} from '../../services/report';
import { getEvents, Event } from '../../services/event';

const { Option } = Select;

type LeaderboardType = 'revenue' | 'profit' | 'roi';

const BoothLeaderboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [booths, setBooths] = useState<LeaderboardItem[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<number | undefined>(undefined);
  const [leaderboardType, setLeaderboardType] = useState<LeaderboardType>('revenue');
  const [limit, setLimit] = useState(10);

  useEffect(() => {
    loadEvents();
  }, []);

  useEffect(() => {
    loadLeaderboard();
  }, [selectedEventId, leaderboardType, limit]);

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
      let data;
      if (leaderboardType === 'revenue') {
        data = await getRevenueLeaderboard(selectedEventId, limit);
      } else if (leaderboardType === 'profit') {
        data = await getProfitLeaderboard(selectedEventId, limit);
      } else {
        data = await getRoiLeaderboard(selectedEventId, limit);
      }
      setBooths(data.leaderboard);
    } catch (error) {
      console.error('Failed to load leaderboard:', error);
      message.error('加载排行榜失败');
    } finally {
      setLoading(false);
    }
  };

  const getRankIcon = (rank: number) => {
    if (rank === 1) return <CrownOutlined style={{ color: '#FFD700', fontSize: '24px' }} />;
    if (rank === 2) return <TrophyOutlined style={{ color: '#C0C0C0', fontSize: '22px' }} />;
    if (rank === 3) return <TrophyOutlined style={{ color: '#CD7F32', fontSize: '20px' }} />;
    return <span style={{ fontWeight: 'bold', fontSize: '16px' }}>{rank}</span>;
  };

  const columns: ColumnsType<LeaderboardItem> = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 100,
      align: 'center',
      render: (rank: number) => getRankIcon(rank),
    },
    {
      title: '摊位名称',
      dataIndex: 'booth_name',
      key: 'booth_name',
      width: 200,
      render: (text: string, record) => (
        <div>
          <div style={{ fontWeight: 'bold', fontSize: '16px' }}>{text}</div>
          <div style={{ fontSize: '12px', color: '#8c8c8c' }}>
            ID: {record.booth_id}
          </div>
        </div>
      ),
    },
    {
      title: '班级名称',
      dataIndex: 'class_name',
      key: 'class_name',
      width: 200,
    },
    {
      title: '指标值',
      dataIndex: 'value',
      key: 'value',
      width: 200,
      align: 'right',
      render: (value: number) => {
        let display = '';
        let color = '#1890ff';
        
        if (leaderboardType === 'revenue') {
          display = `¥${value.toFixed(2)}`;
          color = '#3f8600';
        } else if (leaderboardType === 'profit') {
          display = `¥${value.toFixed(2)}`;
          color = value >= 0 ? '#3f8600' : '#cf1322';
        } else {
          display = `${value.toFixed(2)}%`;
          color = value >= 50 ? '#3f8600' : value >= 30 ? '#1890ff' : '#faad14';
        }
        
        return (
          <Tag color={color} style={{ fontSize: '16px', fontWeight: 'bold', padding: '4px 12px' }}>
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
          <h2>摊位排行榜 🏆</h2>
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
            <span style={{ marginRight: '8px' }}>排行榜类型：</span>
            <Radio.Group value={leaderboardType} onChange={(e) => setLeaderboardType(e.target.value)}>
              <Radio.Button value="revenue">营业额 TOP</Radio.Button>
              <Radio.Button value="profit">利润 TOP</Radio.Button>
              <Radio.Button value="roi">利润率 TOP</Radio.Button>
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
          dataSource={booths}
          rowKey="booth_id"
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

export default BoothLeaderboard;
