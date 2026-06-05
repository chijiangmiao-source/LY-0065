import { useState, useEffect } from 'react'
import { Table, Button, Modal, Form, Input, Select, message, Space, Card, DatePicker, Tag, Row, Col, List, Alert } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, CheckOutlined, CloseOutlined, ExclamationCircleOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import request from '../utils/request'

interface Appointment {
  id: string
  appointment_no: string
  customer_name: string
  phone: string
  service_id: string
  service_name: string
  employee_id?: string
  employee_name?: string
  appointment_date: string
  time_slot: string
  status: string
  created_at: string
}

interface ServiceOption {
  service_id: string
  name: string
  status: string
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

const statusColors: Record<string, string> = {
  '待服务': 'blue',
  '已完成': 'green',
  '已取消': 'red',
}

interface StockCheckItem {
  consumable_no: string
  consumable_name: string
  required: number
  stock: number
  unit: string
  sufficient: boolean
}

interface StockCheckResult {
  has_template: boolean
  items: StockCheckItem[]
  sufficient: boolean
  insufficient_items: Array<{ consumable_no: string; consumable_name: string; required: number; stock: number; unit: string; reason: string }>
}

const Appointment = () => {
  const [data, setData] = useState<Appointment[]>([])
  const [services, setServices] = useState<ServiceOption[]>([])
  const [employees, setEmployees] = useState<EmployeeOption[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingItem, setEditingItem] = useState<Appointment | null>(null)
  const [form] = Form.useForm()
  const [filters, setFilters] = useState({
    customer_name: '',
    status: '',
  })
  const [stockCheckVisible, setStockCheckVisible] = useState(false)
  const [stockCheckResult, setStockCheckResult] = useState<StockCheckResult | null>(null)
  const [pendingCompleteNo, setPendingCompleteNo] = useState<string>('')

  const fetchData = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filters.customer_name) params.append('customer_name', filters.customer_name)
      if (filters.status) params.append('status', filters.status)
      const res = await request.get(`/appointments?${params.toString()}`) as Appointment[]
      setData(res)
    } finally {
      setLoading(false)
    }
  }

  const fetchServices = async () => {
    try {
      const res = await request.get('/services') as ServiceOption[]
      setServices(res.filter(s => s.status === '启用'))
    } catch (error) {
      console.error('Fetch services error:', error)
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
    fetchServices()
    fetchEmployees()
  }, [filters])

  const handleAdd = () => {
    setEditingItem(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record: Appointment) => {
    setEditingItem(record)
    form.setFieldsValue({
      ...record,
      appointment_date: dayjs(record.appointment_date),
    })
    setModalVisible(true)
  }

  const handleDelete = async (id: string) => {
    try {
      await request.delete(`/appointments/${id}`)
      message.success('删除成功')
      fetchData()
    } catch (error) {
      console.error('Delete error:', error)
    }
  }

  const handleComplete = async (appointment_no: string) => {
    try {
      const res = await request.get(`/appointments/${appointment_no}/stock-check`) as StockCheckResult
      setStockCheckResult(res)
      setPendingCompleteNo(appointment_no)
      setStockCheckVisible(true)
    } catch (error) {
      console.error('Stock check error:', error)
    }
  }

  const confirmComplete = async () => {
    if (!pendingCompleteNo) return
    try {
      await request.post(`/appointments/${pendingCompleteNo}/complete`)
      message.success('服务已完成，耗材已自动扣减')
      setStockCheckVisible(false)
      setPendingCompleteNo('')
      fetchData()
    } catch (error) {
      console.error('Complete error:', error)
    }
  }

  const handleCancel = async (id: string) => {
    try {
      await request.post(`/appointments/${id}/cancel`)
      message.success('预约已取消')
      fetchData()
    } catch (error) {
      console.error('Cancel error:', error)
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      const submitData = {
        ...values,
        appointment_date: values.appointment_date.format('YYYY-MM-DD'),
      }
      if (editingItem) {
        await request.put(`/appointments/${editingItem.appointment_no}`, submitData)
        message.success('更新成功')
      } else {
        await request.post('/appointments', submitData)
        message.success('添加成功')
      }
      setModalVisible(false)
      fetchData()
    } catch (error) {
      console.error('Submit error:', error)
    }
  }

  const columns = [
    { title: '预约编号', dataIndex: 'appointment_no', key: 'appointment_no' },
    { title: '客户姓名', dataIndex: 'customer_name', key: 'customer_name' },
    { title: '联系电话', dataIndex: 'phone', key: 'phone' },
    { title: '服务项目', dataIndex: 'service_name', key: 'service_name' },
    { title: '服务员工', dataIndex: 'employee_name', key: 'employee_name' },
    { title: '预约日期', dataIndex: 'appointment_date', key: 'appointment_date' },
    { title: '预约时段', dataIndex: 'time_slot', key: 'time_slot' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => <Tag color={statusColors[status] || 'default'}>{status}</Tag>,
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Appointment) => (
        <Space size="small">
          {record.status === '待服务' && (
            <>
              <Button
                icon={<CheckOutlined />}
                size="small"
                type="primary"
                onClick={() => handleComplete(record.appointment_no)}
              >
                完成
              </Button>
              <Button
                icon={<CloseOutlined />}
                size="small"
                danger
                onClick={() => handleCancel(record.appointment_no)}
              >
                取消
              </Button>
            </>
          )}
          <Button icon={<EditOutlined />} size="small" onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Button
            icon={<DeleteOutlined />}
            size="small"
            danger
            onClick={() => handleDelete(record.appointment_no)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <Card
      title="预约登记"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          新增预约
        </Button>
      }
    >
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Input
              placeholder="搜索客户姓名"
              allowClear
              value={filters.customer_name}
              onChange={(e) => setFilters({ ...filters, customer_name: e.target.value })}
            />
          </Col>
          <Col span={8}>
            <Select
              placeholder="选择状态"
              allowClear
              style={{ width: '100%' }}
              value={filters.status || undefined}
              onChange={(value) => setFilters({ ...filters, status: value || '' })}
              options={[
                { value: '待服务', label: '待服务' },
                { value: '已完成', label: '已完成' },
                { value: '已取消', label: '已取消' },
              ]}
            />
          </Col>
          <Col span={8}>
            <Button onClick={() => setFilters({ customer_name: '', status: '' })}>重置</Button>
          </Col>
        </Row>
      </Card>
      <Table columns={columns} dataSource={data} rowKey="id" loading={loading} />
      <Modal
        title={editingItem ? '编辑预约' : '新增预约'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="appointment_no"
                label="预约编号"
                rules={[{ required: true, message: '请输入预约编号' }]}
              >
                <Input disabled={!!editingItem} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="customer_name"
                label="客户姓名"
                rules={[{ required: true, message: '请输入客户姓名' }]}
              >
                <Input />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="phone"
                label="联系电话"
                rules={[{ required: true, message: '请输入联系电话' }]}
              >
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="service_id"
                label="服务项目"
                rules={[{ required: true, message: '请选择服务项目' }]}
              >
                <Select
                  onChange={(value) => {
                    const service = services.find((s) => s.service_id === value)
                    form.setFieldsValue({ service_name: service?.name || '' })
                  }}
                  options={services.map((s) => ({
                    value: s.service_id,
                    label: s.name,
                  }))}
                />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="service_name" hidden>
            <Input />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="employee_id" label="服务员工">
                <Select
                  onChange={(value) => {
                    const employee = employees.find((e) => e.employee_id === value)
                    form.setFieldsValue({ employee_name: employee?.name || '' })
                  }}
                  options={employees.map((e) => ({
                    value: e.employee_id,
                    label: e.name,
                  }))}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="employee_name" hidden>
                <Input />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="appointment_date"
                label="预约日期"
                rules={[{ required: true, message: '请选择预约日期' }]}
              >
                <DatePicker style={{ width: '100%' }} disabledDate={(d) => d && d.isBefore(dayjs().subtract(1, 'day'))} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="time_slot"
                label="预约时段"
                rules={[{ required: true, message: '请选择预约时段' }]}
              >
                <Select options={timeSlots.map((t) => ({ value: t, label: t }))} />
              </Form.Item>
            </Col>
          </Row>
          {editingItem && (
            <Form.Item name="status" label="状态">
              <Select
                options={[
                  { value: '待服务', label: '待服务' },
                  { value: '已完成', label: '已完成' },
                  { value: '已取消', label: '已取消' },
                ]}
              />
            </Form.Item>
          )}
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              提交
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="服务完成确认 - 耗材库存检查"
        open={stockCheckVisible}
        onCancel={() => setStockCheckVisible(false)}
        onOk={confirmComplete}
        okText="确认完成服务"
        cancelText="取消"
        okButtonProps={{ disabled: !stockCheckResult?.sufficient }}
        width={520}
      >
        {stockCheckResult && (
          <>
            {!stockCheckResult.has_template ? (
              <Alert
                message="该服务项目未配置耗材模板"
                description="完成服务将不会自动扣减任何耗材库存。"
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
            ) : stockCheckResult.sufficient ? (
              <Alert
                message="库存充足，可正常完成服务"
                description="完成服务后将自动扣减以下耗材库存："
                type="success"
                showIcon
                style={{ marginBottom: 16 }}
              />
            ) : (
              <Alert
                message="库存不足，无法完成服务"
                description="请先补充耗材库存后再办理服务完成。"
                type="error"
                showIcon
                icon={<ExclamationCircleOutlined />}
                style={{ marginBottom: 16 }}
              />
            )}

            {stockCheckResult.has_template && stockCheckResult.items.length > 0 && (
              <div>
                <div style={{ fontWeight: 600, marginBottom: 8 }}>耗材清单：</div>
                <List
                  size="small"
                  bordered
                  dataSource={stockCheckResult.items}
                  renderItem={(item) => (
                    <List.Item>
                      <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                        <span>{item.consumable_name}</span>
                        <Space>
                          <span>需要: {item.required} {item.unit}</span>
                          <span>库存: {item.stock} {item.unit}</span>
                          <Tag color={item.sufficient ? 'green' : 'red'}>
                            {item.sufficient ? '充足' : '不足'}
                          </Tag>
                        </Space>
                      </Space>
                    </List.Item>
                  )}
                />
              </div>
            )}

            {stockCheckResult.insufficient_items.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <div style={{ fontWeight: 600, marginBottom: 8, color: '#ff4d4f' }}>库存不足详情：</div>
                <List
                  size="small"
                  bordered
                  dataSource={stockCheckResult.insufficient_items}
                  renderItem={(item) => (
                    <List.Item style={{ color: '#ff4d4f' }}>
                      {item.reason}
                    </List.Item>
                  )}
                />
              </div>
            )}
          </>
        )}
      </Modal>
    </Card>
  )
}

export default Appointment
