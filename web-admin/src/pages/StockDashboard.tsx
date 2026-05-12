/**
 * Stock Market Dashboard - 期末结算与动态市值大屏
 * 
 * 高端深色科技风数据可视化大屏
 * 配色：深蓝 + 银色 + 黑金
 */

import React, { useEffect, useState, useRef } from 'react';
import * as echarts from 'echarts';
import { Card, Statistic, Table, Tag, Space } from 'antd';
import { 
  TrophyOutlined, 
  RiseOutlined, 
  FallOutlined,
  DollarOutlined,
  StockOutlined,
  TeamOutlined 
} from '@ant-design/icons';
import axios from 'axios';
import './StockDashboard.css';

interface BoothData {
  booth_id: number;
  booth_name: string;
  class_name: string;
  revenue: number;
  revenue_yuan: number;
  profit: number;
  profit_yuan: number;
  order_count: number;
  score: number;
  ratio: number;
  sold_shares: number;
  total_investment: number;
  total_investment_yuan: number;
  final_price: number;
  final_price_yuan: number;
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
  const [marketStats, setMarketStats] = useState<MarketStats | null>(null);
  const [boothData, setBoothData] = useState<BoothData[]>([]);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [loading, setLoading] = useState(true);
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  const eventId = 1; // TODO: 从配置或路由获取

  // 更新时钟
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // 加载数据
  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000); // 每5秒刷新
    return () => clearInterval(interval);
  }, []);

  // 初始化图表
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
      }
    };
  }, [boothData]);

  const loadData = async () => {
    try {
      const token = localStorage.getItem('nfc_wallet_token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const baseUrl = import.meta.env.VITE_API_URL || '';

      // 加载市场统计
      const statsRes = await axios.get<MarketStats>(
        `${baseUrl}/api/stock/stats/${eventId}`,
        { headers }
      );
      setMarketStats(statsRes.data);

      // 如果已结算，加载结算数据
      if (statsRes.data.is_settled) {
        const settlementRes = await axios.get<{ booths: BoothData[] }>(
          `${baseUrl}/stocks/settlement/event/${eventId}`,
          { headers }
        );
        // settlement endpoint returns array directly, map to booth data format
        const settlements = Array.isArray(settlementRes.data) ? settlementRes.data : (settlementRes.data.booths || []);
        setBoothData(settlements.map((s: any) => ({
          booth_id: s.booth_id,
          booth_name: s.booth_name,
          class_name: s.class_name,
          revenue: s.revenue || 0,
          revenue_yuan: s.revenue_yuan || 0,
          profit: s.profit || 0,
          profit_yuan: s.profit_yuan || 0,
          order_count: s.order_count || 0,
          score: s.score || 0,
          ratio: s.ratio || 0,
          sold_shares: s.order_count || 0,
          total_investment: s.revenue || 0,
          total_investment_yuan: s.revenue_yuan || 0,
          final_price: s.final_price || 0,
          final_price_yuan: s.final_price_yuan || 0,
        })));
      } else {
        // 未结算，加载实时数据（模拟）
        // TODO: 实现实时数据接口
        setBoothData([]);
      }

      setLoading(false);
    } catch (error) {
      console.error('加载数据失败:', error);
      setLoading(false);
    }
  };

  const updateChart = () => {
    if (!chartInstance.current || boothData.length === 0) return;

    const sortedData = [...boothData].sort((a, b) => b.score - a.score);
    const names = sortedData.map(b => b.booth_name);
    const scores = sortedData.map(b => b.score);

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
          data: scores.map((score, index) => ({
            value: score,
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
              return params.value.toFixed(2);
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
      dataIndex: 'final_price_yuan',
      key: 'final_price_yuan',
      render: (price: number, _record: BoothData, index: number) => {
        const initialPrice = 10.0;
        const change = ((price - initialPrice) / initialPrice) * 100;
        const isUp = change >= 0;
        
        return (
          <div>
            <div className={index === 0 ? 'text-gold text-lg font-bold' : 'text-white text-lg'}>
              ¥{formatNumber(price)}
            </div>
            <div className={isUp ? 'text-green-400' : 'text-red-400'}>
              {isUp ? <RiseOutlined /> : <FallOutlined />}
              {' '}
              {isUp ? '+' : ''}{change.toFixed(2)}%
            </div>
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
      title: '经营分',
      dataIndex: 'score',
      key: 'score',
      render: (score: number, _: any, index: number) => (
        <Tag color={index === 0 ? 'gold' : 'blue'} className="score-tag">
          {formatNumber(score)}
        </Tag>
      ),
    },
  ];

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

        {/* 中央面板 - 经营指数排行 */}
        <div className="center-panel">
          <Card className="data-card chart-card" bordered={false}>
            <div className="card-header">
              <TrophyOutlined className="card-icon" />
              <span>综合经营分排行</span>
            </div>
            <div ref={chartRef} className="chart-container" />
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
                <div className="top-badge">最被看好公司</div>
                <div className="top-name">{boothData[0]?.booth_name}</div>
                <div className="top-price">
                  ¥{formatNumber(boothData[0]?.final_price_yuan || 0)}
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
    </div>
  );
};

export default StockDashboard;
