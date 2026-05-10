import { useState, useEffect } from 'react'
import { Table, Card, Tag, DatePicker, Space, message, Empty, Pagination } from 'antd'
import { getMerchantTransactions, type MerchantTransaction } from '@/services/merchant'
import { useIsMobile } from '@/hooks/useIsMobile'
import dayjs from 'dayjs'
import './merchant-mobile.css'

const { RangePicker } = DatePicker

const MerchantTransactions = () => {
  const [transactions, setTransactions] = useState<MerchantTransaction[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [dateRange, setDateRange] = useState<[string, string] | null>(null)
  const isMobile = useIsMobile()

  useEffect(() => {
    loadTransactions()
  }, [page, dateRange])

  const loadTransactions = async () => {
    setLoading(true)
    try {
      const params: any = {
        limit: pageSize,
        offset: (page - 1) * pageSize,
      }
      if (dateRange) {
        params.start_date = dateRange[0]
        params.end_date = dateRange[1]
      }
      const data = await getMerchantTransactions(params)
      setTransactions(data.transactions)
      setTotalCount(data.total_count)
    } catch (error) {
      message.error('加载交易记录失败')
    } finally {
      setLoading(false)
    }
  }

  const handleDateChange = (_: any, dateStrings: [string, string]) => {
    if (dateStrings[0] && dateStrings[1]) {
      setDateRange(dateStrings)
    } else {
      setDateRange(null)
    }
    setPage(1)
  }

  const typeLabel = (type: string) => {
    const labelMap: Record<string, string> = {
      pay: '收款',
      refund: '退款',
      recharge: '充值',
    }
    return labelMap[type] || type
  }

  const typeColor = (type: string) => {
    const colorMap: Record<string, string> = {
      pay: 'green',
      refund: 'red',
      recharge: 'blue',
    }
    return colorMap[type] || 'default'
  }

  const columns = [
    { title: '交易ID', dataIndex: 'id', key: 'id', width: 80 },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 80,
      render: (type: string) => <Tag color={typeColor(type)}>{typeLabel(type)}</Tag>,
    },
    {
      title: '金额（元）',
      dataIndex: 'amount',
      key: 'amount',
      width: 110,
      render: (amount: number, record: MerchantTransaction) => {
        const color = record.type === 'refund' ? '#cf1322' : '#3f8600'
        const prefix = record.type === 'refund' ? '-' : '+'
        return (
          <span style={{ color, fontWeight: 'bold' }}>
            {prefix}¥{amount.toFixed(2)}
          </span>
        )
      },
    },
    {
      title: '商品',
      dataIndex: 'product_name',
      key: 'product_name',
      width: 140,
      render: (name: string | null) => name || '-',
    },
    {
      title: '备注',
      dataIndex: 'remark',
      key: 'remark',
      width: 150,
      render: (remark: string | null) => remark || '-',
    },
    {
      title: '交易时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
    },
  ]

  const renderMobileList = () => {
    if (loading) {
      return <div style={{ textAlign: 'center', padding: 30 }}>加载中...</div>
    }
    if (transactions.length === 0) {
      return <Empty description="暂无交易记录" />
    }
    return (
      <div>
        {transactions.map((t) => {
          const isRefund = t.type === 'refund'
          const amountColor = isRefund ? '#cf1322' : '#3f8600'
          const amountPrefix = isRefund ? '-' : '+'
          return (
            <div key={t.id} className="merchant-mobile-list-item">
              <div className="merchant-mobile-list-item-header">
                <span>
                  <Tag color={typeColor(t.type)} style={{ marginRight: 8 }}>
                    {typeLabel(t.type)}
                  </Tag>
                  <span style={{ fontSize: 13, color: '#8c8c8c' }}>#{t.id}</span>
                </span>
                <span style={{ color: amountColor, fontSize: 16 }}>
                  {amountPrefix}¥{t.amount.toFixed(2)}
                </span>
              </div>
              {t.product_name && (
                <div className="merchant-mobile-list-item-row">
                  <span className="label">商品</span>
                  <span className="value">{t.product_name}</span>
                </div>
              )}
              {t.remark && (
                <div className="merchant-mobile-list-item-row">
                  <span className="label">备注</span>
                  <span className="value">{t.remark}</span>
                </div>
              )}
              <div className="merchant-mobile-list-item-row">
                <span className="label">时间</span>
                <span className="value">
                  {dayjs(t.created_at).format('YYYY-MM-DD HH:mm:ss')}
                </span>
              </div>
            </div>
          )
        })}
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Pagination
            current={page}
            pageSize={pageSize}
            total={totalCount}
            onChange={(p) => setPage(p)}
            showSizeChanger={false}
            size="small"
            simple
          />
          <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 6 }}>
            共 {totalCount} 条记录
          </div>
        </div>
      </div>
    )
  }

  return (
    <Card
      title="交易记录"
      extra={
        !isMobile && (
          <Space>
            <RangePicker onChange={handleDateChange} />
          </Space>
        )
      }
    >
      {isMobile && (
        <div style={{ marginBottom: 12 }}>
          <RangePicker
            onChange={handleDateChange}
            style={{ width: '100%' }}
            inputReadOnly
          />
        </div>
      )}

      {isMobile ? (
        renderMobileList()
      ) : (
        <Table
          columns={columns}
          dataSource={transactions}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            pageSize,
            total: totalCount,
            onChange: (p) => setPage(p),
            showTotal: (total) => `共 ${total} 条记录`,
            showSizeChanger: false,
          }}
          locale={{ emptyText: '暂无交易记录' }}
          size="middle"
        />
      )}
    </Card>
  )
}

export default MerchantTransactions
