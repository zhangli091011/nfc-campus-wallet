/**
 * Stock Market Dashboard - 股市实时交易大屏
 * 
 * 高端深色科技风数据可视化大屏
 * 配色：深蓝 + 银色 + 黑金
 * 
 * 功能：
 * 1. 先获取活动列表，选择活动后展示数据
 * 2. 实时刷新市场统计和摊位数据
 */

import React, { useEffect, useState, useRef, useCallback } from 'react';
import * as echarts from 'echarts';
import { Card, Statistic, Table, Tag, Space, Select, Spin, Empty } from 'antd';
import { 
  TrophyOutlined, 
  RiseOutlined, 
  FallOutlined,
  DollarOutlined,
  StockOutlined,
  TeamOutlined 
} from '@ant-design/icons';
import request from '@/utils/request';
import './StockDashboard.css';

interface EventItem {
  id: number;
  name: string;
  status: string;
  start_date: string;
  end_date: string;
}

interface BoothData {
  booth_id: number;
  booth_name: string;
  class_name: string;
  sold_shares: number;
  total_investment: number;
  total_investment_yuan: number;
  investor_count: number;
  current_price: number;
  is_settled: boolean;
  final_price: number | null;
  final_price_yuan: number | null;
}

interface MarketStats {
  event_id: number;
  total_investment: number;
  total_investment_yuan: number;
  global_pool: number;
  global_pool_yuan: number;
  fee_collected: number;
  fee_collected_yuan: number;
  total_orders: number;
  total_investors: number;
  total_booths: number;
  is_settled: boolean;
  total_sold_orders?: number;
  total_sold_shares?: number;
  total_sold_amount?: number;
}

const StockDashboard: React.FC = () => {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<number | null>(null);
  const [marketStats, setMarketStats] = useState<MarketStats | null>(null);
  const [boothData, setBoothData] = useState<BoothData[]>([]);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [loading, setLoading] = useState(false);
  const [eventsLoading, setEventsLoading] = useState(true);
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const refreshTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  // 更新时钟
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // 加载活动列表
  useEffect(() => {
    loadEvents();
  }, []);

  // 选择活动后加载数据
  useEffect(() => {
    if (selectedEventId) {
      loadData();
      // 每5秒刷新
      if (refreshTimer.current) {
        clearInterval(refreshTimer.current);
      }
      refreshTimer.current = setInterval(loadData, 5000);
    }
    return () => {
      if (refreshTimer.current) {
        clearInterval(refreshTimer.current);
      }
    };
  }, [selectedEventId]);

  // 初始化/更新图表
  useEffect(() => {
    if (chartRef.current && boothData.length > 0) {
      if (!chartInstance.current) {
        chartInstance.current = echarts.init(chartRef.current);
      }
      updateChart();
    }
    return () => {
      if (chartInstance.current) {
        chartInstance.current.dispose();
        chartInstance.current = null;
      }
    };
  }, [boothData]);

  // 窗口大小变化时重新调整图表
  useEffect(() => {
    const handleResize = () => {
      if (chartInstance.current) {
        chartInstance.current.resize();
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const loadEvents = async () => {
    try {
      setEventsLoading(true);
      const res: any = await request.get('/events');
      const eventList = res.events || res || [];
      setEvents(eventList);
      // 自动选择第一个活动（优先选active的）
      if (eventList.length > 0) {
        const activeEvent = eventList.find((e: EventItem) => e.status === 'active');
        setSelectedEventId(activeEvent ? activeEvent.id : eventList[0].id);
      }
    } catch (error) {
      console.error('加载活动列表失败:', error);
    } finally {
      setEventsLoading(false);
    }
  };

  const loadData = useCallback(async () => {
    if (!selectedEventId) return;
    
    try {
      setLoading(true);

      // 并行加载市场统计和摊位数据
      const [statsRes, boothRes] = await Promise.all([
        request.get(`/stock/stats/${selectedEventId}`).catch(() => null),
        request.get(`/stock/all-booth-stats/${selectedEventId}`).catch(() => []),
      ]);

      if (statsRes) {
        setMarketStats(statsRes as any);
      }

      const booths = Array.isArray(boothRes) ? boothRes : [];
      setBoothData(booths as BoothData[]);
    } catch (error) {
      console.error('加载数据失败:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedEventId]);

  const updateChart = () => {
    if (!chartInstance.current || boothData.length === 0) return;

    // 按总投资额排序
    const sortedData = [...boothData].sort((a, b) => b.total_investment_yuan - a.total_investment_yuan);
    const names = sortedData.map(b => `${b.booth_name}`);
    const investments = sortedData.map(b => b.total_investment_yuan);

    const option: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      grid: {
        left: '15%',
        right: '10%',
        top: '5%',
        bottom: '5%',
      },
      xAxis: {
        type: 'value',
        axisLine: {
          lineStyle: {
            color: '#2A4A7C',
          },
        },
        axisLabel: {
          color: '#8B9DC3',
          fontSize: 12,
        },
        splitLine: {
          lineStyle: {
            color: '#1A2F4F',
            type: 'dashed',
          },
        },
      },
      yAxis: {
        type: 'category',
        data: names,
        axisLine: {
          lineStyle: {
            color: '#2A4A7C',
          },
        },
        axisLabel: {
          color: '#C0C0C0',
          fontSize: 14,
          fontWeight: 'bold',
        },
        axisTick: {
          show: false,
        },
      },
      series: [
        {
          type: 'bar',
          data: investments.map((val, index) => ({
            value: val,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                { offset: 0, color: index === 0 ? '#FFD700' : '#4A90E2' },
                { offset: 1, color: index === 0 ? '#FFA500' : '#2E5C8A' },
              ]),
              borderRadius: [0, 4, 4, 0],
            },
          })),
          barWidth: '60%',
          label: {
            show: true,
            position: 'right',
            color: '#FFD700',
            fontSize: 14,
            fontWeight: 'bold',
            formatter: (params: any) => {
              return `¥${params.value.toFixed(2)}`;
            },
          },
          animationDuration: 1000,
          animationEasing: 'cubicOut',
        },
      ],
    };

    chartInstance.current.setOption(option, true);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('zh-CN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(num);
  };

  const columns = [
    {
      title: '排名',
      key: 'rank',
      width: 80,
      render: (_: any, _record: BoothData, index: number) => (
        <div className="rank-badge">
          {index === 0 ? (
            <TrophyOutlined style={{ color: '#FFD700', fontSize: 24 }} />
          ) : (
            <span className="rank-number">{index + 1}</span>
          )}
        </div>
      ),
    },
    {
      title: '摊位名称',
      dataIndex: 'booth_name',
      key: 'booth_name',
      render: (text: string, record: BoothData, index: number) => (
        <div>
          <div className={index === 0 ? 'text-gold font-bold' : 'text-white font-semibold'}>
            {text}
          </div>
          <div className="text-gray-400 text-sm">{record.class_name}</div>
        </div>
      ),
    },
    {
      title: '当前股价',
      key: 'price',
      render: (_: any, record: BoothData, index: number) => {
        const price = record.final_price_yuan ?? record.current_price;
        const initialPrice = 10.0;
        const change = ((price - initialPrice) / initialPrice) * 100;
        const isUp = change >= 0;
        
        return (
          <div>
            <div className={index === 0 ? 'text-gold text-lg font-bold' : 'text-white text-lg'}>
              ¥{formatNumber(price)}
            </div>
            {record.is_settled && (
              <div className={isUp ? 'text-green-400' : 'text-red-400'}>
                {isUp ? <RiseOutlined /> : <FallOutlined />}
                {' '}
                {isUp ? '+' : ''}{change.toFixed(2)}%
              </div>
            )}
          </div>
        );
      },
    },
    {
      title: '售出股数',
      dataIndex: 'sold_shares',
      key: 'sold_shares',
      render: (shares: number) => (
        <span className="text-white">{shares} 股</span>
      ),
    },
    {
      title: '总投资额',
      dataIndex: 'total_investment_yuan',
      key: 'total_investment_yuan',
      render: (amount: number) => (
        <span className="text-blue-300">¥{formatNumber(amount)}</span>
      ),
    },
    {
      title: '投资人数',
      dataIndex: 'investor_count',
      key: 'investor_count',
      render: (count: number) => (
        <Tag color="blue" className="score-tag">
          {count} 人
        </Tag>
      ),
    },
  ];

  // 活动选择界面
  if (eventsLoading) {
    return (
      <div className="stock-dashboard" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <Spin size="large" tip="加载活动列表..." />
      </div>
    );
  }

  return (
    <div className="stock-dashboard">
      {/* 顶部标题栏 */}
      <div className="dashboard-header">
        <div className="header-content">
          <div className="title-section">
            <StockOutlined className="title-icon" />
            <h1 className="dashboard-title">模拟市场实时交易大屏</h1>
          </div>
          <div className="status-section">
            <Select
              value={selectedEventId}
              onChange={(val) => setSelectedEventId(val)}
              style={{ width: 220, marginRight: 16 }}
              placeholder="选择活动"
              options={events.map(e => ({
                value: e.id,
                label: `${e.name} (${e.status === 'active' ? '进行中' : e.status})`,
              }))}
              dropdownStyle={{ background: '#1a2332' }}
            />
            <div className="status-indicator">
              <div className={`status-light ${marketStats?.is_settled ? 'settled' : 'active'}`} />
              <span className="status-text">
                {marketStats?.is_settled ? '已结算' : '交易中'}
              </span>
            </div>
            <div className="clock">
              {currentTime.toLocaleTimeString('zh-CN', { hour12: false })}
            </div>
          </div>
        </div>
      </div>

      {/* 主要内容区 */}
      {!selectedEventId ? (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
          <Empty description="请选择一个活动" />
        </div>
      ) : (
        <div className="dashboard-content">
          {/* 左侧面板 - 宏观资金池 */}
          <div className="left-panel">
            <Card className="data-card pool-card" bordered={false}>
              <div className="card-header">
                <DollarOutlined className="card-icon" />
                <span>全局奖金池</span>
              </div>
              <div className="pool-amount">
                <div className="amount-label">当前奖金池</div>
                <div className="amount-value gold-glow">
                  ¥{formatNumber(marketStats?.global_pool_yuan || 0)}
                </div>
              </div>
              <div className="pool-stats">
                <div className="stat-item">
                  <span className="stat-label">总投资额</span>
                  <span className="stat-value">
                    ¥{formatNumber(marketStats?.total_investment_yuan || 0)}
                  </span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">手续费</span>
                  <span className="stat-value">
                    ¥{formatNumber(marketStats?.fee_collected_yuan || 0)}
                  </span>
                </div>
              </div>
            </Card>

            <Card className="data-card stats-card" bordered={false}>
              <div className="card-header">
                <TeamOutlined className="card-icon" />
                <span>市场概况</span>
              </div>
              <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <Statistic
                  title={<span className="stat-title">参与摊位</span>}
                  value={marketStats?.total_booths || 0}
                  suffix="个"
                  valueStyle={{ color: '#4A90E2', fontSize: 32 }}
                />
                <Statistic
                  title={<span className="stat-title">投资人数</span>}
                  value={marketStats?.total_investors || 0}
                  suffix="人"
                  valueStyle={{ color: '#50C878', fontSize: 32 }}
                />
                <Statistic
                  title={<span className="stat-title">买入订单</span>}
                  value={marketStats?.total_orders || 0}
                  suffix="笔"
                  valueStyle={{ color: '#9370DB', fontSize: 32 }}
                />
                <Statistic
                  title={<span className="stat-title">抛售订单</span>}
                  value={marketStats?.total_sold_orders || 0}
                  suffix="笔"
                  valueStyle={{ color: '#FF6B35', fontSize: 32 }}
                />
              </Space>
            </Card>
          </div>

          {/* 中央面板 - 投资额排行 */}
          <div className="center-panel">
            <Card className="data-card chart-card" bordered={false}>
              <div className="card-header">
                <TrophyOutlined className="card-icon" />
                <span>摊位投资额排行</span>
              </div>
              {boothData.length > 0 ? (
                <div ref={chartRef} className="chart-container" />
              ) : (
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                  <Empty description="暂无股票交易数据" />
                </div>
              )}
            </Card>
          </div>

          {/* 右侧面板 - 模拟股价看板 */}
          <div className="right-panel">
            <Card className="data-card table-card" bordered={false}>
              <div className="card-header">
                <RiseOutlined className="card-icon" />
                <span>股价实时看板</span>
              </div>
              {boothData.length > 0 && (
                <div className="top-company">
                  <div className="top-badge">最受投资者青睐</div>
                  <div className="top-name">{boothData[0]?.booth_name}</div>
                  <div className="top-price">
                    ¥{formatNumber(boothData[0]?.total_investment_yuan || 0)}
                  </div>
                </div>
              )}
              <Table
                columns={columns}
                dataSource={boothData}
                rowKey="booth_id"
                pagination={false}
                loading={loading}
                className="stock-table"
                scroll={{ y: 500 }}
              />
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

export default StockDashboard;
