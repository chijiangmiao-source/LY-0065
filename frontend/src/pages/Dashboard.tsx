import { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, Table, Tag } from 'antd'
import {
  CalendarOutlined, TeamOutlined, InboxOutlined, CheckCircleOutlined, WarningOutlined,
  LineChartOutlined, CrownOutlined, WalletOutlined, RiseOutlined
} from '@ant-design/icons'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell,
  ResponsiveContainer, LineChart, Line
} from 'recharts'
import request from '../utils/request'

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d']

interface AppointmentStats {
  total: number
  pending: number
  completed: number
  cancelled: number
  by_status: Record<string, number>
}

interface ScheduleDistribution {
  total: number
  by_employee: Record<string, number>
  by_date: Record<string, number>
}

interface ConsumableRanking {
  ranking: Array<{ name: string; quantity: number; rank: number }>
}

interface DashboardSummary {
  today: {
    appointments: number
    schedules: number
  }
  total: {
    appointments: number
    schedules: number
  }
  appointment_status: Record<string, number>
  low_stock_count: number
  members: {
    total_members: number
    total_balance: number
    total_recharge_amount: number
  }
}

interface LowStockItem {
  id: string
  consumable_no: string
  name: string
  stock_quantity: number
  warning_threshold: number
  unit: string
  stock_status: string
  status: string
  gap: number
}

interface LowStockWarning {
  total: number
  items: LowStockItem[]
}

interface UsageTrendData {
  date: string
  label: string
  total: number
  自动扣减: number
  手工: number
}

interface Usage7DayTrend {
  trend: UsageTrendData[]
  summary: {
    total: number
    auto_deduct: number
    manual: number
  }
}

interface RechargeTrendData {
  date: string
  label: string
  recharge_amount: number
  gift_amount: number
  total: number
  count: number
}

interface Recharge7DayTrend {
  trend: RechargeTrendData[]
  summary: {
    total_recharge: number
    total_gift: number
    grand_total: number
  }
}

interface ConsumptionRanking {
  ranking: Array<{ name: string; total_amount: number; count: number; rank: number }>
}

const Dashboard = () => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [appointmentStats, setAppointmentStats] = useState<AppointmentStats | null>(null)
  const [scheduleDistribution, setScheduleDistribution] = useState<ScheduleDistribution | null>(null)
  const [consumableRanking, setConsumableRanking] = useState<ConsumableRanking | null>(null)
  const [lowStockWarning, setLowStockWarning] = useState<LowStockWarning | null>(null)
  const [usageTrend, setUsageTrend] = useState<Usage7DayTrend | null>(null)
  const [rechargeTrend, setRechargeTrend] = useState<Recharge7DayTrend | null>(null)
  const [consumptionRanking, setConsumptionRanking] = useState<ConsumptionRanking | null>(null)

  const fetchSummary = async () => {
    try {
      const res = await request.get('/dashboard/summary') as DashboardSummary
      setSummary(res)
    } catch (error) {
      console.error('Fetch summary error:', error)
    }
  }

  const fetchLowStockWarning = async () => {
    try {
      const res = await request.get('/dashboard/consumables/low-stock') as LowStockWarning
      setLowStockWarning(res)
    } catch (error) {
      console.error('Fetch low stock warning error:', error)
    }
  }

  const fetchUsageTrend = async () => {
    try {
      const res = await request.get('/dashboard/usages/7-day-trend') as Usage7DayTrend
      setUsageTrend(res)
    } catch (error) {
      console.error('Fetch usage trend error:', error)
    }
  }

  const fetchRechargeTrend = async () => {
    try {
      const res = await request.get('/dashboard/members/recharge-7-day-trend') as Recharge7DayTrend
      setRechargeTrend(res)
    } catch (error) {
      console.error('Fetch recharge trend error:', error)
    }
  }

  const fetchConsumptionRanking = async () => {
    try {
      const res = await request.get('/dashboard/members/consumption-ranking') as ConsumptionRanking
      setConsumptionRanking(res)
    } catch (error) {
      console.error('Fetch consumption ranking error:', error)
    }
  }

  const fetchStats = async () => {
    try {
      const [appointmentRes, scheduleRes, consumableRes] = await Promise.all([
        request.get('/dashboard/appointments/count') as Promise<AppointmentStats>,
        request.get('/dashboard/schedules/distribution') as Promise<ScheduleDistribution>,
        request.get('/dashboard/consumables/ranking') as Promise<ConsumableRanking>,
      ])
      setAppointmentStats(appointmentRes)
      setScheduleDistribution(scheduleRes)
      setConsumableRanking(consumableRes)
    } catch (error) {
      console.error('Fetch stats error:', error)
    }
  }

  useEffect(() => {
    fetchSummary()
    fetchStats()
    fetchLowStockWarning()
    fetchUsageTrend()
    fetchRechargeTrend()
    fetchConsumptionRanking()
  }, [])

  const appointmentChartData = appointmentStats
    ? Object.entries(appointmentStats.by_status).map(([name, value]) => ({ name, value }))
    : []

  const scheduleChartData = scheduleDistribution
    ? Object.entries(scheduleDistribution.by_employee).map(([name, value]) => ({ name, 排班数量: value }))
    : []

  const rankingColumns = [
    { title: '排名', dataIndex: 'rank', key: 'rank', width: 80 },
    { title: '耗材名称', dataIndex: 'name', key: 'name' },
    { title: '消耗数量', dataIndex: 'quantity', key: 'quantity' },
  ]

  const lowStockColumns = [
    { title: '耗材编号', dataIndex: 'consumable_no', key: 'consumable_no' },
    { title: '耗材名称', dataIndex: 'name', key: 'name' },
    {
      title: '当前库存',
      dataIndex: 'stock_quantity',
      key: 'stock_quantity',
      render: (val: number, record: LowStockItem) => `${val} ${record.unit}`,
    },
    {
      title: '预警阈值',
      dataIndex: 'warning_threshold',
      key: 'warning_threshold',
      render: (val: number, record: LowStockItem) => `${val} ${record.unit}`,
    },
    {
      title: '缺口',
      dataIndex: 'gap',
      key: 'gap',
      render: (val: number, record: LowStockItem) => (
        <Tag color="red">差 {val} {record.unit}</Tag>
      ),
    },
    {
      title: '库存状态',
      dataIndex: 'stock_status',
      key: 'stock_status',
      render: (status: string) => (
        <Tag color={status === '缺货' ? 'red' : 'orange'}>{status}</Tag>
      ),
    },
  ]

  const memberRankingColumns = [
    { title: '排名', dataIndex: 'rank', key: 'rank', width: 80 },
    { title: '会员姓名', dataIndex: 'name', key: 'name' },
    { title: '消费次数', dataIndex: 'count', key: 'count' },
    {
      title: '消费金额',
      dataIndex: 'total_amount',
      key: 'total_amount',
      render: (val: number) => <span style={{ fontWeight: 600, color: '#f5222d' }}>¥{val.toFixed(2)}</span>,
    },
  ]

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="今日预约"
              value={summary?.today.appointments || 0}
              prefix={<CalendarOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="今日排班"
              value={summary?.today.schedules || 0}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="会员总数"
              value={summary?.members.total_members || 0}
              prefix={<CrownOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="储值总额"
              value={summary?.members.total_balance || 0}
              precision={2}
              prefix={<WalletOutlined />}
              suffix="元"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="总预约数"
              value={summary?.total.appointments || 0}
              prefix={<CalendarOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="累计充值"
              value={summary?.members.total_recharge_amount || 0}
              precision={2}
              prefix={<RiseOutlined />}
              suffix="元"
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="低库存预警"
              value={summary?.low_stock_count || 0}
              prefix={<WarningOutlined />}
              valueStyle={{ color: summary?.low_stock_count ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card
            title={<span><WarningOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />低库存预警列表</span>}
            extra={<span>共 {lowStockWarning?.total || 0} 种耗材</span>}
          >
            <Table
              columns={lowStockColumns}
              dataSource={lowStockWarning?.items || []}
              rowKey="id"
              pagination={{ pageSize: 5 }}
              size="small"
              locale={{ emptyText: '暂无低库存耗材，库存状态良好' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card title="预约状态分布">
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={appointmentChartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {appointmentChartData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col span={8}>
          <Card title="员工排班分布">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={scheduleChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="排班数量" fill="#1890ff" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col span={8}>
          <Card
            title={<span><CrownOutlined style={{ marginRight: 8 }} />会员消费排行</span>}
          >
            <Table
              columns={memberRankingColumns}
              dataSource={consumptionRanking?.ranking || []}
              rowKey="rank"
              pagination={false}
              size="small"
              locale={{ emptyText: '暂无会员消费数据' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card
            title={<span><LineChartOutlined style={{ marginRight: 8 }} />近7日耗材扣减趋势</span>}
            extra={
              <span>
                近7日总扣减: <strong>{usageTrend?.summary.total || 0}</strong>
                ，自动扣减: <Tag color="blue">{usageTrend?.summary.auto_deduct || 0}</Tag>
                ，手工: <Tag color="green">{usageTrend?.summary.manual || 0}</Tag>
              </span>
            }
          >
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={usageTrend?.trend || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="label" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="自动扣减" stroke="#1890ff" strokeWidth={2} />
                <Line type="monotone" dataKey="手工" stroke="#52c41a" strokeWidth={2} />
                <Line type="monotone" dataKey="total" stroke="#722ed1" strokeWidth={2} strokeDasharray="5 5" name="合计" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col span={12}>
          <Card
            title={<span><WalletOutlined style={{ marginRight: 8 }} />近7日会员充值趋势</span>}
            extra={
              <span>
                充值合计: <strong style={{ color: '#52c41a' }}>¥{rechargeTrend?.summary.total_recharge?.toFixed(2) || '0.00'}</strong>
                ，赠送: <Tag color="orange">¥{rechargeTrend?.summary.total_gift?.toFixed(2) || '0.00'}</Tag>
              </span>
            }
          >
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={rechargeTrend?.trend || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="label" />
                <YAxis />
                <Tooltip formatter={(value: any, name: any) =>
                  name === 'count' ? [value, '笔数'] : [`¥${Number(value).toFixed(2)}`, name]
                } />
                <Legend formatter={(value: any) => {
                  if (value === 'recharge_amount') return '充值金额'
                  if (value === 'gift_amount') return '赠送金额'
                  if (value === 'total') return '合计'
                  if (value === 'count') return '充值笔数'
                  return value
                }} />
                <Bar dataKey="recharge_amount" fill="#52c41a" name="充值金额" />
                <Bar dataKey="gift_amount" fill="#faad14" name="赠送金额" />
                <Line type="monotone" dataKey="total" stroke="#1890ff" strokeWidth={2} name="合计" yAxisId={0} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={24}>
          <Card title="耗材消耗排行" extra={<InboxOutlined />}>
            <Table
              columns={rankingColumns}
              dataSource={consumableRanking?.ranking || []}
              rowKey="rank"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
