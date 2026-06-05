import { useState, useEffect } from 'react'
import { Table, Button, Modal, Form, Input, Select, message, Space, Card, InputNumber, DatePicker, Row, Col } from 'antd'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import request from '../utils/request'

interface Usage {
  id: string
  usage_no: string
  consumable_no: string
  consumable_name: string
  quantity: number
  employee_id: string
  employee_name: string
  usage_date: string
  remark?: string
  created_at: string
}

interface ConsumableOption {
  consumable_no: string
  name: string
  stock_quantity: number
}

interface EmployeeOption {
  employee_id: string
  name: string
}

const Usage = () => {
  const [data, setData] = useState<Usage[]>([])
  const [consumables, setConsumables] = useState<ConsumableOption[]>([])
  const [employees, setEmployees] = useState<EmployeeOption[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [form] = Form.useForm()
  const [filters, setFilters] = useState({
    consumable_name: '',
    employee_id: '',
    usage_date: '',
  })

  const fetchData = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filters.consumable_name) params.append('consumable_name', filters.consumable_name)
      if (filters.employee_id) params.append('employee_id', filters.employee_id)
      if (filters.usage_date) params.append('usage_date', filters.usage_date)
      const res = await request.get(`/usages?${params.toString()}`) as Usage[]
      setData(res)
    } finally {
      setLoading(false)
    }
  }

  const fetchConsumables = async () => {
    try {
      const res = await request.get('/consumables') as ConsumableOption[]
      setConsumables(res.filter(c => c.status === '正常' && c.stock_quantity > 0))
    } catch (error) {
      console.error('Fetch consumables error:', error)
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
    fetchConsumables()
    fetchEmployees()
  }, [filters])

  const handleAdd = () => {
    form.resetFields()
    setModalVisible(true)
  }

  const handleDelete = async (id: string) => {
    try {
      await request.delete(`/usages/${id}`)
      message.success('删除成功')
      fetchData()
      fetchConsumables()
    } catch (error) {
      console.error('Delete error:', error)
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      const consumable = consumables.find(c => c.consumable_no === values.consumable_no)
      const employee = employees.find(e => e.employee_id === values.employee_id)
      const submitData = {
        ...values,
        consumable_name: consumable?.name || '',
        employee_name: employee?.name || '',
        usage_date: values.usage_date.format('YYYY-MM-DD'),
      }
      await request.post('/usages', submitData)
      message.success('领用成功')
      setModalVisible(false)
      fetchData()
      fetchConsumables()
    } catch (error) {
      console.error('Submit error:', error)
    }
  }

  const columns = [
    { title: '领用编号', dataIndex: 'usage_no', key: 'usage_no' },
    { title: '耗材名称', dataIndex: 'consumable_name', key: 'consumable_name' },
    { title: '耗材编号', dataIndex: 'consumable_no', key: 'consumable_no' },
    { title: '领用数量', dataIndex: 'quantity', key: 'quantity' },
    { title: '领用人', dataIndex: 'employee_name', key: 'employee_name' },
    { title: '领用日期', dataIndex: 'usage_date', key: 'usage_date' },
    { title: '备注', dataIndex: 'remark', key: 'remark' },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Usage) => (
        <Space>
          <Button
            icon={<DeleteOutlined />}
            size="small"
            danger
            onClick={() => handleDelete(record.usage_no)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <Card
      title="领用登记"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          新增领用
        </Button>
      }
    >
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Input
              placeholder="搜索耗材名称"
              allowClear
              value={filters.consumable_name}
              onChange={(e) => setFilters({ ...filters, consumable_name: e.target.value })}
            />
          </Col>
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
              onChange={(date) => setFilters({ ...filters, usage_date: date ? date.format('YYYY-MM-DD') : '' })}
            />
          </Col>
        </Row>
      </Card>
      <Table columns={columns} dataSource={data} rowKey="id" loading={loading} />
      <Modal
        title="新增领用"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
            name="usage_no"
            label="领用编号"
            rules={[{ required: true, message: '请输入领用编号' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="consumable_no"
            label="耗材"
            rules={[{ required: true, message: '请选择耗材' }]}
          >
            <Select
              options={consumables.map((c) => ({
                value: c.consumable_no,
                label: `${c.name} (库存: ${c.stock_quantity})`,
              }))}
            />
          </Form.Item>
          <Form.Item
            name="quantity"
            label="领用数量"
            rules={[{ required: true, message: '请输入领用数量' }]}
          >
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="employee_id"
            label="领用人"
            rules={[{ required: true, message: '请选择领用人' }]}
          >
            <Select
              options={employees.map((e) => ({
                value: e.employee_id,
                label: e.name,
              }))}
            />
          </Form.Item>
          <Form.Item
            name="usage_date"
            label="领用日期"
            rules={[{ required: true, message: '请选择领用日期' }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={3} />
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

export default Usage
