import { useState, useEffect } from 'react'
import { Table, Button, Modal, Form, Select, message, Space, Card, DatePicker, Row, Col, Input } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import request from '../utils/request'

interface Schedule {
  id: string
  schedule_id: string
  employee_id: string
  employee_name: string
  schedule_date: string
  time_slot: string
  created_at: string
}

interface EmployeeOption {
  employee_id: string
  name: string
  status: string
}

const timeSlots = [
  '09:00-10:00',
  '10:00-11:00',
  '11:00-12:00',
  '13:00-14:00',
  '14:00-15:00',
  '15:00-16:00',
  '16:00-17:00',
  '17:00-18:00',
  '18:00-19:00',
  '19:00-20:00',
]

const Schedule = () => {
  const [data, setData] = useState<Schedule[]>([])
  const [employees, setEmployees] = useState<EmployeeOption[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingItem, setEditingItem] = useState<Schedule | null>(null)
  const [form] = Form.useForm()
  const [filters, setFilters] = useState({
    employee_id: '',
    schedule_date: '',
  })

  const fetchData = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filters.employee_id) params.append('employee_id', filters.employee_id)
      if (filters.schedule_date) params.append('schedule_date', filters.schedule_date)
      const res = await request.get(`/schedules?${params.toString()}`) as Schedule[]
      setData(res)
    } finally {
      setLoading(false)
    }
  }

  const fetchEmployees = async () => {
    try {
      const res = await request.get('/employees') as EmployeeOption[]
      setEmployees(res.filter(e => e.status === '在职'))
    } catch (error) {
      console.error('Fetch employees error:', error)
    }
  }

  useEffect(() => {
    fetchData()
    fetchEmployees()
  }, [filters])

  const handleAdd = () => {
    setEditingItem(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record: Schedule) => {
    setEditingItem(record)
    form.setFieldsValue({
      ...record,
      schedule_date: dayjs(record.schedule_date),
    })
    setModalVisible(true)
  }

  const handleDelete = async (id: string) => {
    try {
      await request.delete(`/schedules/${id}`)
      message.success('删除成功')
      fetchData()
    } catch (error) {
      console.error('Delete error:', error)
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      const employee = employees.find(e => e.employee_id === values.employee_id)
      const submitData = {
        ...values,
        employee_name: employee?.name || '',
        schedule_date: values.schedule_date.format('YYYY-MM-DD'),
      }
      if (editingItem) {
        await request.put(`/schedules/${editingItem.schedule_id}`, submitData)
        message.success('更新成功')
      } else {
        await request.post('/schedules', submitData)
        message.success('添加成功')
      }
      setModalVisible(false)
      fetchData()
    } catch (error) {
      console.error('Submit error:', error)
    }
  }

  const columns = [
    { title: '排班编号', dataIndex: 'schedule_id', key: 'schedule_id' },
    { title: '员工姓名', dataIndex: 'employee_name', key: 'employee_name' },
    { title: '员工编号', dataIndex: 'employee_id', key: 'employee_id' },
    { title: '排班日期', dataIndex: 'schedule_date', key: 'schedule_date' },
    { title: '排班时段', dataIndex: 'time_slot', key: 'time_slot' },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Schedule) => (
        <Space>
          <Button icon={<EditOutlined />} size="small" onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Button
            icon={<DeleteOutlined />}
            size="small"
            danger
            onClick={() => handleDelete(record.schedule_id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <Card
      title="排班管理"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          新增排班
        </Button>
      }
    >
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Select
              placeholder="选择员工"
              allowClear
              style={{ width: '100%' }}
              value={filters.employee_id || undefined}
              onChange={(value) => setFilters({ ...filters, employee_id: value || '' })}
              options={employees.map((e) => ({
                value: e.employee_id,
                label: e.name,
              }))}
            />
          </Col>
          <Col span={8}>
            <DatePicker
              placeholder="选择日期"
              style={{ width: '100%' }}
              onChange={(date) => setFilters({ ...filters, schedule_date: date ? date.format('YYYY-MM-DD') : '' })}
            />
          </Col>
          <Col span={8}>
            <Button onClick={() => setFilters({ employee_id: '', schedule_date: '' })}>重置</Button>
          </Col>
        </Row>
      </Card>
      <Table columns={columns} dataSource={data} rowKey="id" loading={loading} />
      <Modal
        title={editingItem ? '编辑排班' : '新增排班'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
            name="schedule_id"
            label="排班编号"
            rules={[{ required: true, message: '请输入排班编号' }]}
          >
            <Input disabled={!!editingItem} />
          </Form.Item>
          <Form.Item
            name="employee_id"
            label="员工"
            rules={[{ required: true, message: '请选择员工' }]}
          >
            <Select
              options={employees.map((e) => ({
                value: e.employee_id,
                label: e.name,
              }))}
            />
          </Form.Item>
          <Form.Item
            name="schedule_date"
            label="排班日期"
            rules={[{ required: true, message: '请选择排班日期' }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="time_slot"
            label="排班时段"
            rules={[{ required: true, message: '请选择排班时段' }]}
          >
            <Select options={timeSlots.map((t) => ({ value: t, label: t }))} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              提交
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}

export default Schedule
