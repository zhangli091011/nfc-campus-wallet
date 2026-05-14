/**
 * Stock Market Dashboard - 股市实时交易大屏
 *
 * 高端深色科技风数据可视化大屏
 * 配色：深蓝 + 银色 + 黑金
 *
 * 功能：
 * 1. 顶部滚动跑马灯实时显示所有股价
 * 2. K线图展示选中摊位的真实Pari-mutuel价格走势
 * 3. 全市场对比折线图
 * 4. 实时刷新（每10秒）
 */

import React, { useEffect, useState, useRef, useCallback, useMemo } from 'react';
import * as echarts from 'echarts';
import { Card, Statistic, Table, Tag, Space, Select, Spin, Empty } from 'antd';
import {
  TrophyOutlined,
  RiseOutlined,
  FallOutlined,
  DollarOutlined,
  StockOutlined,
  TeamOutlined,
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

interface KlinePoint {
  time: string;
  open: number;
  close: number;
  high: number;
  low: number;
  volume: number;
}

interface BoothKline {
  booth_id: number;
  booth_name: string;
  class_name: string;
  kline: KlinePoint[];
}

interface PriceItem {
  booth_id: number;
  booth_name: string;
  class_name: string;
  current_price: number;
  base_price: number;
  change_percent: number;
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

// 一组好看的颜色用于多摊位折线
const LINE_COLORS = [
  '#FFD700', '#4A90E2', '#50C878', '#FF6B35', '#9370DB',
  '#FF4D4F', '#13C2C2', '#FAAD14', '#722ED1', '#52C41A',
  '#EB2F96', '#1890FF', '#FA8C16', '#A0D911', '#F5222D',
];

const StockDashboard: React.FC = () => {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<number | null>(null);
  const [marketStats, setMarketStats] = useState<MarketStats | null>(null);
  const [boothData, setBoothData] = useState<BoothData[]>([]);
  const [klineData, setKlineData] = useState<BoothKline[]>([]);
  const [tickerData, setTickerData] = useState<PriceItem[]>([]);
  const [selectedBooth, setSelectedBooth] = useState<number | null>(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [loading, setLoading] = useState(false);
  const [eventsLoading, setEventsLoading] = useState(true);
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const refreshTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const tickerTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  // 加载活动列表
  const loadEvents = useCallback(async () => {
    try {
      setEventsLoading(true);
      const res: any = await request.get('/events');
      const eventList = res.events || res || [];
      setEvents(eventList);
      if (eventList.length > 0) {
        const activeEvent = eventList.find((e: EventItem) => e.status === 'active');
        setSelectedEventId(activeEvent ? activeEvent.id : eventList[0].id);
      }
    } catch (error) {
      console.error('加载活动列表失败:', error);
    } finally {
      setEventsLoading(false);
    }
  }, []);

  // 加载实时股价（高频刷新）
  const loadTickerPrices = useCallback(async () => {
    if (!selectedEventId) return;
    try {
      const res: any = await request.get(`/stock/prices/${selectedEventId}`);
      const prices = Array.isArray(res) ? res : [];
      setTickerData(prices as PriceItem[]);
    } catch (error) {
      // ticker 失败不阻塞
    }
  }, [selectedEventId]);

  // 加载市场数据 + K线
  const loadData = useCallback(async () => {
    if (!selectedEventId) return;
    try {
      setLoading(true);
      const [statsRes, boothRes, klineRes] = await Promise.all([
        request.get(`/stock/stats/${selectedEventId}`).catch(() => null),
        request.get(`/stock/all-booth-stats/${selectedEventId}`).catch(() => []),
        request.get(`/stock/kline/${selectedEventId}?interval=5`).catch(() => []),
      ]);
      if (statsRes) {
        setMarketStats(statsRes as any);
      }
      const booths = Array.isArray(boothRes) ? boothRes : [];
      setBoothData(booths as BoothData[]);

      const klines = Array.isArray(klineRes) ? klineRes : [];
      setKlineData(klines as BoothKline[]);
    } catch (error) {
      console.error('加载数据失败:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedEventId]);

  // 更新K线图表
  const updateChart = useCallback(() => {
    if (!chartInstance.current || klineData.length === 0) return;

    if (selectedBooth) {
      // 单摊位K线
      const boothKline = klineData.find(k => k.booth_id === selectedBooth);
      if (!boothKline || boothKline.kline.length === 0) {
        chartInstance.current.clear();
        return;
      }

      const times = boothKline.kline.map(k => k.time);
      // ECharts 蜡烛图数据格式: [open, close, low, high]
      const ohlc = boothKline.kline.map(k => [k.open, k.close, k.low, k.high]);
      const volumes = boothKline.kline.map(k => k.volume);
      const closes = boothKline.kline.map(k => k.close);

      const option: echarts.EChartsOption = {
        backgroundColor: 'transparent',
        animation: false,
        title: {
          text: `${boothKline.booth_name} - K线走势`,
          left: 'center',
          textStyle: { color: '#FFD700', fontSize: 16, fontWeight: 'bold' },
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross' },
          backgroundColor: 'rgba(10, 20, 40, 0.95)',
          borderColor: '#2A4A7C',
          textStyle: { color: '#C0C0C0' },
        },
        legend: {
          data: ['K线', 'MA5', '成交量'],
          top: 30,
          textStyle: { color: '#8B9DC3' },
        },
        grid: [
          { left: '10%', right: '5%', top: '15%', height: '55%' },
          { left: '10%', right: '5%', top: '75%', height: '15%' },
        ],
        xAxis: [
          {
            type: 'category',
            data: times,
            boundaryGap: true,
            axisLine: { lineStyle: { color: '#2A4A7C' } },
            axisLabel: { color: '#8B9DC3', fontSize: 11 },
            splitLine: { show: false },
          },
          {
            type: 'category',
            gridIndex: 1,
            data: times,
            axisLine: { lineStyle: { color: '#2A4A7C' } },
            axisLabel: { show: false },
            splitLine: { show: false },
          },
        ],
        yAxis: [
          {
            type: 'value',
            scale: true,
            axisLine: { lineStyle: { color: '#2A4A7C' } },
            axisLabel: {
              color: '#8B9DC3',
              formatter: (val: number) => `¥${val.toFixed(2)}`,
            },
            splitLine: { lineStyle: { color: '#1A2F4F', type: 'dashed' } },
          },
          {
            type: 'value',
            gridIndex: 1,
            scale: true,
            axisLine: { lineStyle: { color: '#2A4A7C' } },
            axisLabel: { color: '#8B9DC3', fontSize: 10 },
            splitLine: { show: false },
          },
        ],
        dataZoom: [
          {
            type: 'inside',
            xAxisIndex: [0, 1],
            start: Math.max(0, 100 - (50 / Math.max(times.length, 1)) * 100),
            end: 100,
          },
        ],
        series: [
          {
            name: 'K线',
            type: 'candlestick',
            data: ohlc,
            itemStyle: {
              color: '#EF5350',       // 涨：红
              color0: '#26A69A',      // 跌：绿
              borderColor: '#EF5350',
              borderColor0: '#26A69A',
            },
          },
          {
            name: 'MA5',
            type: 'line',
            data: calcMA(closes, 5),
            smooth: true,
            symbol: 'none',
            lineStyle: { width: 1.5, color: '#FFD700' },
          },
          {
            name: '成交量',
            type: 'bar',
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: volumes,
            itemStyle: {
              color: (params: any) => {
                const idx = params.dataIndex;
                const k = boothKline.kline[idx];
                return k.close >= k.open ? 'rgba(239, 83, 80, 0.7)' : 'rgba(38, 166, 154, 0.7)';
              },
            },
          },
        ],
      };

      chartInstance.current.setOption(option, true);
    } else {
      // 全市场对比折线
      // 找到最长的时间序列作为统一X轴
      const longestKline = klineData.reduce((longest, curr) =>
        curr.kline.length > longest.kline.length ? curr : longest
      );
      const allTimes = longestKline.kline.map(k => k.time);

      const series = klineData.slice(0, 15).map((booth, index) => ({
        name: booth.booth_name,
        type: 'line' as const,
        data: booth.kline.map(k => k.close),
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2 },
        emphasis: { focus: 'series' as const },
        itemStyle: { color: LINE_COLORS[index % LINE_COLORS.length] },
      }));

      const option: echarts.EChartsOption = {
        backgroundColor: 'transparent',
        animation: false,
        title: {
          text: '全市场股价走势',
          left: 'center',
          textStyle: { color: '#FFD700', fontSize: 16, fontWeight: 'bold' },
        },
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(10, 20, 40, 0.95)',
          borderColor: '#2A4A7C',
          textStyle: { color: '#C0C0C0' },
          axisPointer: { type: 'cross' },
        },
        legend: {
          bottom: 0,
          textStyle: { color: '#8B9DC3', fontSize: 11 },
          type: 'scroll',
          pageTextStyle: { color: '#8B9DC3' },
        },
        grid: { left: '8%', right: '5%', top: '15%', bottom: '15%' },
        xAxis: {
          type: 'category',
          data: allTimes,
          boundaryGap: false,
          axisLine: { lineStyle: { color: '#2A4A7C' } },
          axisLabel: { color: '#8B9DC3', fontSize: 11 },
          splitLine: { show: false },
        },
        yAxis: {
          type: 'value',
          scale: true,
          axisLine: { lineStyle: { color: '#2A4A7C' } },
          axisLabel: {
            color: '#8B9DC3',
            formatter: (val: number) => `¥${val.toFixed(1)}`,
          },
          splitLine: { lineStyle: { color: '#1A2F4F', type: 'dashed' } },
        },
        series,
      };

      chartInstance.current.setOption(option, true);
    }
  }, [klineData, selectedBooth]);

  // 更新时钟
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // 初始加载活动列表
  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  // 选择活动后加载数据并定时刷新
  useEffect(() => {
    if (selectedEventId) {
      loadData();
      loadTickerPrices();
      if (refreshTimer.current) clearInterval(refreshTimer.current);
      refreshTimer.current = setInterval(loadData, 30000); // K线30秒
      if (tickerTimer.current) clearInterval(tickerTimer.current);
      tickerTimer.current = setInterval(loadTickerPrices, 10000); // 跑马灯10秒
    }
    return () => {
      if (refreshTimer.current) clearInterval(refreshTimer.current);
      if (tickerTimer.current) clearInterval(tickerTimer.current);
    };
  }, [selectedEventId, loadData, loadTickerPrices]);

  // 初始化图表实例（只一次）
  useEffect(() => {
    if (chartRef.current && !chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current);
    }
    return () => {
      if (chartInstance.current) {
        chartInstance.current.dispose();
        chartInstance.current = null;
      }
    };
  }, []);

  // K线数据变化时更新
  useEffect(() => {
    if (chartInstance.current) {
      updateChart();
    }
  }, [klineData, selectedBooth, updateChart]);

  // 窗口大小变化时重新调整图表
  useEffect(() => {
    const handleResize = () => chartInstance.current?.resize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('zh-CN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(num);
  };

  // 跑马灯：复制一份数据实现无缝循环
  const tickerItems = useMemo(() => {
    if (tickerData.length === 0) return [];
    return [...tickerData, ...tickerData];
  }, [tickerData]);

  const columns = [
    {
      title: '排名',
      key: 'rank',
      width: 60,
      render: (_: any, _record: BoothData, index: number) => (
        <div className="rank-badge">
          {index === 0 ? (
            <TrophyOutlined style={{ color: '#FFD700', fontSize: 20 }} />
          ) : (
            <span className="rank-number">{index + 1}</span>
          )}
        </div>
      ),
    },
    {
      title: '摊位',
      dataIndex: 'booth_name',
      key: 'booth_name',
      render: (text: string, record: BoothData, index: number) => (
        <div
          style={{ cursor: 'pointer' }}
          onClick={() => setSelectedBooth(record.booth_id === selectedBooth ? null : record.booth_id)}
        >
          <div className={index === 0 ? 'text-gold font-bold' : 'text-white font-semibold'}>
            {text}
          </div>
          <div className="text-gray-400 text-sm">{record.class_name}</div>
        </div>
      ),
    },
    {
      title: '股价',
      key: 'price',
      width: 100,
      render: (_: any, record: BoothData) => {
        const price = record.final_price_yuan ?? record.current_price;
        const initialPrice = 5.0;
        const change = ((price - initialPrice) / initialPrice) * 100;
        const isUp = change >= 0;
        return (
          <div>
            <div className="text-white">¥{formatNumber(price)}</div>
            <div className={isUp ? 'text-red-400 text-xs' : 'text-green-400 text-xs'}>
              {isUp ? <RiseOutlined /> : <FallOutlined />}{' '}
              {isUp ? '+' : ''}
              {change.toFixed(1)}%
            </div>
          </div>
        );
      },
    },
    {
      title: '股数',
      dataIndex: 'sold_shares',
      key: 'sold_shares',
      width: 70,
      render: (shares: number) => <span className="text-white">{shares}</span>,
    },
    {
      title: '投资额',
      dataIndex: 'total_investment_yuan',
      key: 'total_investment_yuan',
      width: 100,
      render: (amount: number) => <span className="text-blue-300">¥{formatNumber(amount)}</span>,
    },
  ];

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

      {/* 实时股价滚动跑马灯 */}
      {selectedEventId && tickerData.length > 0 && (
        <div className="stock-ticker">
          <div className="ticker-track">
            {tickerItems.map((item, idx) => {
              const isUp = item.change_percent > 0;
              const isFlat = item.change_percent === 0;
              return (
                <div
                  key={`${item.booth_id}-${idx}`}
                  className="ticker-item"
                  onClick={() => setSelectedBooth(item.booth_id === selectedBooth ? null : item.booth_id)}
                >
                  <span className="ticker-name">{item.booth_name}</span>
                  <span className="ticker-price">¥{item.current_price.toFixed(2)}</span>
                  <span className={`ticker-change ${isFlat ? 'flat' : isUp ? 'up' : 'down'}`}>
                    <span className="ticker-arrow">{isFlat ? '—' : isUp ? '▲' : '▼'}</span>
                    {isUp ? '+' : ''}
                    {item.change_percent.toFixed(2)}%
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 主要内容区 */}
      {!selectedEventId ? (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
          <Empty description="请选择一个活动" />
        </div>
      ) : (
        <div className="dashboard-content">
          {/* 左侧面板 */}
          <div className="left-panel">
            <Card className="data-card pool-card" variant="borderless">
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
                  <span className="stat-value">¥{formatNumber(marketStats?.total_investment_yuan || 0)}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">手续费</span>
                  <span className="stat-value">¥{formatNumber(marketStats?.fee_collected_yuan || 0)}</span>
                </div>
              </div>
            </Card>

            <Card className="data-card stats-card" variant="borderless">
              <div className="card-header">
                <TeamOutlined className="card-icon" />
                <span>市场概况</span>
              </div>
              <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <Statistic
                  title={<span className="stat-title">参与摊位</span>}
                  value={marketStats?.total_booths || 0}
                  suffix="个"
                  valueStyle={{ color: '#4A90E2', fontSize: 28 }}
                />
                <Statistic
                  title={<span className="stat-title">投资人数</span>}
                  value={marketStats?.total_investors || 0}
                  suffix="人"
                  valueStyle={{ color: '#50C878', fontSize: 28 }}
                />
                <Statistic
                  title={<span className="stat-title">买入订单</span>}
                  value={marketStats?.total_orders || 0}
                  suffix="笔"
                  valueStyle={{ color: '#9370DB', fontSize: 28 }}
                />
                <Statistic
                  title={<span className="stat-title">抛售订单</span>}
                  value={marketStats?.total_sold_orders || 0}
                  suffix="笔"
                  valueStyle={{ color: '#FF6B35', fontSize: 28 }}
                />
              </Space>
            </Card>
          </div>

          {/* 中央面板 - K线图 */}
          <div className="center-panel">
            <Card className="data-card chart-card" variant="borderless">
              <div className="card-header">
                <StockOutlined className="card-icon" />
                <span>
                  {selectedBooth
                    ? `${klineData.find(k => k.booth_id === selectedBooth)?.booth_name || ''} K线走势`
                    : '全市场股价走势'}
                </span>
                {selectedBooth && (
                  <Tag
                    color="gold"
                    style={{ marginLeft: 12, cursor: 'pointer' }}
                    onClick={() => setSelectedBooth(null)}
                  >
                    查看全部 ×
                  </Tag>
                )}
              </div>
              {klineData.length > 0 ? (
                <div ref={chartRef} className="chart-container" />
              ) : (
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '500px' }}>
                  <Empty description="暂无股票交易数据" />
                </div>
              )}
            </Card>
          </div>

          {/* 右侧面板 - 股价看板 */}
          <div className="right-panel">
            <Card className="data-card table-card" variant="borderless">
              <div className="card-header">
                <RiseOutlined className="card-icon" />
                <span>股价实时看板</span>
              </div>
              {boothData.length > 0 && (
                <div className="top-company">
                  <div className="top-badge">最受投资者青睐</div>
                  <div className="top-name">{boothData[0]?.booth_name}</div>
                  <div className="top-price">¥{formatNumber(boothData[0]?.total_investment_yuan || 0)}</div>
                </div>
              )}
              <Table
                columns={columns}
                dataSource={boothData}
                rowKey="booth_id"
                pagination={false}
                loading={loading}
                className="stock-table"
                scroll={{ y: 400 }}
                size="small"
                onRow={(record) => ({
                  onClick: () =>
                    setSelectedBooth(record.booth_id === selectedBooth ? null : record.booth_id),
                  style: {
                    cursor: 'pointer',
                    background:
                      record.booth_id === selectedBooth ? 'rgba(255, 215, 0, 0.1)' : undefined,
                  },
                })}
              />
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

// 计算移动平均线
function calcMA(data: number[], dayCount: number): (number | null)[] {
  const result: (number | null)[] = [];
  for (let i = 0; i < data.length; i++) {
    if (i < dayCount - 1) {
      result.push(null);
      continue;
    }
    let sum = 0;
    for (let j = 0; j < dayCount; j++) {
      sum += data[i - j];
    }
    result.push(+(sum / dayCount).toFixed(2));
  }
  return result;
}

export default StockDashboard;
