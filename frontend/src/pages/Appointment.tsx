import { useState, useEffect } from 'react'
import { Table, Button, Modal, Form, Input, Select, message, Space, Card, DatePicker, Tag, Row, Col, List, Alert, Descriptions, Statistic } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, CheckOutlined, CloseOutlined, ExclamationCircleOutlined, WalletOutlined, DollarOutlined } from '@ant-design/icons'
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
  pay_method?: string
  member_no?: string
  pay_amount?: number
  discount_rate?: number
  created_at: string
}

interface ServiceOption {
  service_id: string
  name: string
  price: number
  status: string
}

interface EmployeeOption {
  employee_id: string
  name: string
  status: string
}

interface MemberOption {
  member_no: string
  name: string
  phone: string
  level_name: string
  balance: number
  discount_rate: number
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

const AppointmentPage = () => {
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

  const [payVisible, setPayVisible] = useState(false)
  const [payMethod, setPayMethod] = useState<'余额' | '现金'>('现金')
  const [selectedMember, setSelectedMember] = useState<MemberOption | null>(null)
  const [memberSearchPhone, setMemberSearchPhone] = useState('')
  const [memberSearching, setMemberSearching] = useState(false)
  const [currentService, setCurrentService] = useState<ServiceOption | null>(null)
  const [completingAppointment, setCompletingAppointment] = useState<Appointment | null>(null)

  const actualAmount = (() => {
    if (!currentService) return 0
    if (payMethod === '余额' && selectedMember) {
      return Math.round(currentService.price * selectedMember.discount_rate * 100) / 100
    }
    return currentService.price
  })()

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

  const handleComplete = async (record: Appointment) => {
    setCompletingAppointment(record)
    const service = services.find(s => s.service_id === record.service_id)
    setCurrentService(service || null)
    setPayMethod('现金')
    setSelectedMember(null)
    setMemberSearchPhone(record.phone)
    try {
      const res = await request.get(`/appointments/${record.appointment_no}/stock-check`) as StockCheckResult
      setStockCheckResult(res)
      setPendingCompleteNo(record.appointment_no)
      setStockCheckVisible(true)
    } catch (error) {
      console.error('Stock check error:', error)
    }
  }

  const goToPay = () => {
    setStockCheckVisible(false)
    setPayVisible(true)
  }

  const searchMemberByPhone = async () => {
    if (!memberSearchPhone) {
      message.warning('请输入手机号')
      return
    }
    setMemberSearching(true)
    try {
      const member = await request.get(`/members/phone/${memberSearchPhone}`) as MemberOption
      const level = await request.get(`/members/levels/${(member as any).level_id}`) as any
      setSelectedMember({
        ...member,
        discount_rate: level?.discount_rate ?? 1.0,
      })
      message.success(`找到会员：${member.name}`)
    } catch (error) {
      setSelectedMember(null)
      message.error('未找到该手机号对应的会员')
    } finally {
      setMemberSearching(false)
    }
  }

  const confirmComplete = async () => {
    if (!pendingCompleteNo) return
    try {
      const payload: any = { pay_method: payMethod }
      if (payMethod === '余额') {
        if (!selectedMember) {
          message.error('余额支付请先选择会员')
          return
        }
        if (selectedMember.balance < actualAmount) {
          message.error(`会员余额不足，当前余额 ¥${selectedMember.balance.toFixed(2)}，需支付 ¥${actualAmount.toFixed(2)}`)
          return
        }
        if (selectedMember.phone !== completingAppointment?.phone) {
          message.error('会员手机号与预约手机号不一致')
          return
        }
        payload.member_no = selectedMember.member_no
      }
      await request.post(`/appointments/${pendingCompleteNo}/complete`, payload)
      message.success(payMethod === '余额'
        ? `服务已完成，已从会员余额扣除 ¥${actualAmount.toFixed(2)}`
        : `服务已完成，现金支付 ¥${actualAmount.toFixed(2)}`
      )
      setPayVisible(false)
      setStockCheckVisible(false)
      setPendingCompleteNo('')
      setCompletingAppointment(null)
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
      title: '支付信息',
      key: 'pay_info',
      render: (_: any, record: Appointment) => (
        record.status === '已完成' ? (
          <Space>
            <Tag color={record.pay_method === '余额' ? 'blue' : 'green'}>{record.pay_method}</Tag>
            {record.pay_amount !== undefined && <span style={{ fontWeight: 600 }}>¥{record.pay_amount.toFixed(2)}</span>}
          </Space>
        ) : '-'
      ),
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
                onClick={() => handleComplete(record)}
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
                    label: `${s.name} (¥${s.price})`,
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
        onOk={stockCheckResult?.sufficient ? goToPay : undefined}
        okText="去支付"
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

      <Modal
        title="服务完成 - 选择支付方式"
        open={payVisible}
        onCancel={() => setPayVisible(false)}
        onOk={confirmComplete}
        okText="确认完成支付"
        width={560}
      >
        {completingAppointment && currentService && (
          <>
            <Descriptions size="small" column={2} bordered style={{ marginBottom: 16 }}>
              <Descriptions.Item label="预约编号">{completingAppointment.appointment_no}</Descriptions.Item>
              <Descriptions.Item label="客户姓名">{completingAppointment.customer_name}</Descriptions.Item>
              <Descriptions.Item label="联系电话">{completingAppointment.phone}</Descriptions.Item>
              <Descriptions.Item label="服务项目">{currentService.name}</Descriptions.Item>
              <Descriptions.Item label="服务原价" contentStyle={{ color: '#999' }}>¥{currentService.price.toFixed(2)}</Descriptions.Item>
              <Descriptions.Item label="实付金额" contentStyle={{ color: '#f5222d', fontWeight: 600, fontSize: 18 }}>
                ¥{actualAmount.toFixed(2)}
                {payMethod === '余额' && selectedMember && selectedMember.discount_rate < 1 && (
                  <Tag color="orange" style={{ marginLeft: 8 }}>
                    {(selectedMember.discount_rate * 10).toFixed(1)}折优惠
                  </Tag>
                )}
              </Descriptions.Item>
            </Descriptions>

            <div style={{ marginBottom: 16 }}>
              <div style={{ fontWeight: 600, marginBottom: 8 }}>支付方式：</div>
              <Space>
                <Button
                  type={payMethod === '现金' ? 'primary' : 'default'}
                  icon={<DollarOutlined />}
                  onClick={() => setPayMethod('现金')}
                >
                  现金支付
                </Button>
                <Button
                  type={payMethod === '余额' ? 'primary' : 'default'}
                  icon={<WalletOutlined />}
                  onClick={() => setPayMethod('余额')}
                >
                  会员余额支付
                </Button>
              </Space>
            </div>

            {payMethod === '余额' && (
              <Card size="small" type="inner" title="会员信息">
                <Row gutter={8} style={{ marginBottom: 12 }}>
                  <Col span={16}>
                    <Input
                      placeholder="输入会员手机号搜索"
                      value={memberSearchPhone}
                      onChange={(e) => setMemberSearchPhone(e.target.value)}
                      onPressEnter={searchMemberByPhone}
                    />
                  </Col>
                  <Col span={8}>
                    <Button type="primary" onClick={searchMemberByPhone} loading={memberSearching} block>
                      搜索会员
                    </Button>
                  </Col>
                </Row>
                {selectedMember ? (
                  <Alert
                    type="success"
                    showIcon
                    message={
                      <Space>
                        <span>会员：<strong>{selectedMember.name}</strong></span>
                        <Tag color="purple">{selectedMember.level_name}</Tag>
                      </Space>
                    }
                    description={
                      <Space>
                        <span>余额：<strong style={{ color: '#52c41a' }}>¥{selectedMember.balance.toFixed(2)}</strong></span>
                        <span>折扣：<Tag color="orange">{(selectedMember.discount_rate * 10).toFixed(1)}折</Tag></span>
                        {selectedMember.balance < actualAmount && (
                          <Tag color="red">余额不足，需 ¥{actualAmount.toFixed(2)}</Tag>
                        )}
                      </Space>
                    }
                  />
                ) : (
                  <Alert
                    type="warning"
                    showIcon
                    message="请先搜索并选择会员"
                    description="余额支付需要验证会员身份和余额"
                  />
                )}
              </Card>
            )}
          </>
        )}
      </Modal>
    </Card>
  )
}

export default AppointmentPage
