import { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, DatePicker, Table } from 'antd'
import { CalendarOutlined, TeamOutlined, InboxOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'
import dayjs from 'dayjs'
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
}

const Dashboard = () => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [appointmentStats, setAppointmentStats] = useState<AppointmentStats | null>(null)
  const [scheduleDistribution, setScheduleDistribution] = useState<ScheduleDistribution | null>(null)
  const [consumableRanking, setConsumableRanking] = useState<ConsumableRanking | null>(null)
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs | null, dayjs.Dayjs | null] | null>(null)

  const fetchSummary = async () => {
    try {
      const res = await request.get('/dashboard/summary') as DashboardSummary
      setSummary(res)
    } catch (error) {
      console.error('Fetch summary error:', error)
    }
  }

  const fetchStats = async () => {
    try {
      const params = new URLSearchParams()
      if (dateRange && dateRange[0]) {
        params.append('start_date', dateRange[0].format('YYYY-MM-DD'))
      }
      if (dateRange && dateRange[1]) {
        params.append('end_date', dateRange[1].format('YYYY-MM-DD'))
      }
      const [appointmentRes, scheduleRes, consumableRes] = await Promise.all([
        request.get(`/dashboard/appointments/count?${params.toString()}`) as Promise<AppointmentStats>,
        request.get(`/dashboard/schedules/distribution?${params.toString()}`) as Promise<ScheduleDistribution>,
        request.get(`/dashboard/consumables/ranking?${params.toString()}`) as Promise<ConsumableRanking>,
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
  }, [dateRange])

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

  return (
    <div>
      <div style={{ marginBottom: 16, textAlign: 'right' }}>
        <DatePicker.RangePicker
          onChange={(dates) => setDateRange(dates as [dayjs.Dayjs | null, dayjs.Dayjs | null] | null)}
        />
      </div>

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
              title="总预约数"
              value={summary?.total.appointments || 0}
              prefix={<CalendarOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总排班数"
              value={summary?.total.schedules || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#eb2f96' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card title="预约状态分布">
            <ResponsiveContainer width="100%" height={300}>
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
        <Col span={12}>
          <Card title="员工排班分布">
            <ResponsiveContainer width="100%" height={300}>
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
