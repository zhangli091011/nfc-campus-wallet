/**
 * Reports Dashboard Page
 * 
 * 报表看板页：展示总览统计和关键指标
 */

import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Select, Spin, message, Button } from 'antd';
import {
  DollarOutlined,
  ShoppingOutlined,
  UserOutlined,
  ShopOutlined,
  DownloadOutlined,
} from '@ant-design/icons';
import { getSummaryReport, exportReportExcel, downloadExcel, SummaryReport } from '../../services/report';
import { getEvents, Event } from '../../services/event';

const { Option } = Select;

const ReportsDashboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [summary, setSummary] = useState<SummaryReport | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<number | undefined>(undefined);

  // 加载活动列表
  useEffect(() => {
    loadEvents();
  }, []);

  // 加载总览数据
  useEffect(() => {
    loadSummary();
  }, [selectedEventId]);

  const loadEvents = async () => {
    try {
      const data = await getEvents();
      setEvents(data.events);
    } catch (error) {
      console.error('Failed to load events:', error);
    }
  };

  const loadSummary = async () => {
    setLoading(true);
    try {
      const data = await getSummaryReport(selectedEventId);
      setSummary(data);
    } catch (error) {
      console.error('Failed to load summary:', error);
      message.error('加载总览数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const blob = await exportReportExcel('summary', selectedEventId);
      const filename = `总览统计_${selectedEventId || '全部'}_${new Date().toISOString().split('T')[0]}.xlsx`;
      downloadExcel(blob, filename);
      message.success('导出成功');
    } catch (error) {
      console.error('Failed to export:', error);
      message.error('导出失败');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>报表看板</h1>
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

      <Spin spinning={loading}>
        {summary && (
          <>
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} lg={6}>
                <Card>
                  <Statistic
                    title="总发放额度"
                    value={summary.total_issued}
                    precision={2}
                    prefix={<DollarOutlined />}
                    suffix="元"
                    valueStyle={{ color: '#3f8600' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Card>
                  <Statistic
                    title="总充值额"
                    value={summary.total_recharged}
                    precision={2}
                    prefix={<DollarOutlined />}
                    suffix="元"
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Card>
                  <Statistic
                    title="总消费额"
                    value={summary.total_consumed}
                    precision={2}
                    prefix={<ShoppingOutlined />}
                    suffix="元"
                    valueStyle={{ color: '#cf1322' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Card>
                  <Statistic
                    title="总退款额"
                    value={summary.total_refunded}
                    precision={2}
                    prefix={<DollarOutlined />}
                    suffix="元"
                    valueStyle={{ color: '#faad14' }}
                  />
                </Card>
              </Col>
            </Row>

            <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
              <Col xs={24} sm={12} lg={6}>
                <Card>
                  <Statistic
                    title="净消费额"
                    value={summary.net_consumed}
                    precision={2}
                    prefix={<DollarOutlined />}
                    suffix="元"
                    valueStyle={{ color: '#722ed1' }}
                  />
                  <div style={{ marginTop: '8px', fontSize: '12px', color: '#8c8c8c' }}>
                    = 总消费 - 总退款
                  </div>
                </Card>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Card>
                  <Statistic
                    title="总交易笔数"
                    value={summary.total_transactions}
                    prefix={<ShoppingOutlined />}
                    suffix="笔"
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Card>
                  <Statistic
                    title="参与者数量"
                    value={summary.participant_count}
                    prefix={<UserOutlined />}
                    suffix="人"
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Card>
                  <Statistic
                    title="摊位数量"
                    value={summary.booth_count}
                    prefix={<ShopOutlined />}
                    suffix="个"
                  />
                </Card>
              </Col>
            </Row>
          </>
        )}
      </Spin>
    </div>
  );
};

export default ReportsDashboard;
