import { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Table, Tag, Spin, message, Empty } from 'antd'
import {
  DollarOutlined,
  RiseOutlined,
  ShoppingCartOutlined,
  CalendarOutlined,
} from '@ant-design/icons'
import {
  getMerchantIncome,
  getMerchantTransactions,
  type MerchantIncomeStats,
  type MerchantTransaction,
} from '@/services/merchant'
import { useIsMobile } from '@/hooks/useIsMobile'
import dayjs from 'dayjs'
import './merchant-mobile.css'

const MerchantDashboard = () => {
  const [income, setIncome] = useState<MerchantIncomeStats | null>(null)
  const [transactions, setTransactions] = useState<MerchantTransaction[]>([])
  const [loading, setLoading] = useState(true)
  const isMobile = useIsMobile()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [incomeData, txnData] = await Promise.all([
        getMerchantIncome(),
        getMerchantTransactions({ limit: 10 }),
      ])
      setIncome(incomeData)
      setTransactions(txnData.transactions)
    } catch (error) {
      message.error('加载数据失败')
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    { title: '交易ID', dataIndex: 'id', key: 'id', width: 80 },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 80,
      render: (type: string) => {
        const colorMap: Record<string, string> = { pay: 'green', refund: 'red' }
        const labelMap: Record<string, string> = { pay: '收款', refund: '退款' }
        return <Tag color={colorMap[type] || 'default'}>{labelMap[type] || type}</Tag>
      },
    },
    {
      title: '金额（元）',
      dataIndex: 'amount',
      key: 'amount',
      width: 100,
      render: (amount: number) => (
        <span style={{ color: '#52c41a', fontWeight: 'bold' }}>¥{amount.toFixed(2)}</span>
      ),
    },
    {
      title: '商品',
      dataIndex: 'product_name',
      key: 'product_name',
      width: 120,
      render: (name: string | null) => name || '-',
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (time: string) => dayjs(time).format('MM-DD HH:mm:ss'),
    },
  ]

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
      </div>
    )
  }

  const renderMobileTxnList = () => {
    if (transactions.length === 0) {
      return <Empty description="暂无交易记录" />
    }
    return (
      <div>
        {transactions.map((t) => {
          const isRefund = t.type === 'refund'
          const amountColor = isRefund ? '#cf1322' : '#3f8600'
          return (
            <div key={t.id} className="merchant-mobile-list-item">
              <div className="merchant-mobile-list-item-header">
                <span>
                  <Tag color={isRefund ? 'red' : 'green'} style={{ marginRight: 8 }}>
                    {isRefund ? '退款' : '收款'}
                  </Tag>
                  <span style={{ fontSize: 12, color: '#8c8c8c' }}>#{t.id}</span>
                </span>
                <span style={{ color: amountColor, fontSize: 16 }}>
                  {isRefund ? '-' : '+'}¥{t.amount.toFixed(2)}
                </span>
              </div>
              {t.product_name && (
                <div className="merchant-mobile-list-item-row">
                  <span className="label">商品</span>
                  <span className="value">{t.product_name}</span>
                </div>
              )}
              <div className="merchant-mobile-list-item-row">
                <span className="label">时间</span>
                <span className="value">{dayjs(t.created_at).format('MM-DD HH:mm:ss')}</span>
              </div>
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div>
      <Row gutter={[12, 12]}>
        <Col xs={12} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总收入"
              value={income?.total_income || 0}
              precision={2}
              prefix={<DollarOutlined />}
              suffix="元"
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总交易笔数"
              value={income?.total_transactions || 0}
              prefix={<ShoppingCartOutlined />}
              suffix="笔"
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} lg={6}>
          <Card>
            <Statistic
              title="今日收入"
              value={income?.today_income || 0}
              precision={2}
              prefix={<RiseOutlined />}
              suffix="元"
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} lg={6}>
          <Card>
            <Statistic
              title="今日交易"
              value={income?.today_transactions || 0}
              prefix={<CalendarOutlined />}
              suffix="笔"
            />
          </Card>
        </Col>
      </Row>

      <Card title="最近交易" style={{ marginTop: isMobile ? 12 : 24 }}>
        {isMobile ? (
          renderMobileTxnList()
        ) : (
          <Table
            columns={columns}
            dataSource={transactions}
            rowKey="id"
            pagination={false}
            size="small"
            locale={{ emptyText: '暂无交易记录' }}
          />
        )}
      </Card>
    </div>
  )
}

export default MerchantDashboard
