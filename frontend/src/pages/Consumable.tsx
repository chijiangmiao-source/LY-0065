import { useState, useEffect } from 'react'
import { Table, Button, Modal, Form, Input, Select, message, Space, Card, InputNumber, Row, Col, Tag } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, InboxOutlined } from '@ant-design/icons'
import request from '../utils/request'

interface Consumable {
  id: string
  consumable_no: string
  name: string
  stock_quantity: number
  warning_threshold: number
  applicable_services: string[]
  unit: string
  status: string
  stock_status: string
  created_at: string
}

interface ServiceOption {
  service_id: string
  name: string
  status: string
}

const stockStatusColors: Record<string, string> = {
  '正常': 'green',
  '库存不足': 'orange',
  '缺货': 'red',
}

const businessStatusColors: Record<string, string> = {
  '正常': 'blue',
  '停用': 'default',
}

const Consumable = () => {
  const [data, setData] = useState<Consumable[]>([])
  const [services, setServices] = useState<ServiceOption[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [stockModalVisible, setStockModalVisible] = useState(false)
  const [editingItem, setEditingItem] = useState<Consumable | null>(null)
  const [selectedConsumable, setSelectedConsumable] = useState<string>('')
  const [form] = Form.useForm()
  const [stockForm] = Form.useForm()
  const [filters, setFilters] = useState({
    name: '',
    status: '',
  })

  const fetchData = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filters.name) params.append('name', filters.name)
      if (filters.status) params.append('status', filters.status)
      const res = await request.get(`/consumables?${params.toString()}`) as Consumable[]
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

  useEffect(() => {
    fetchData()
    fetchServices()
  }, [filters])

  const handleAdd = () => {
    setEditingItem(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record: Consumable) => {
    setEditingItem(record)
    form.setFieldsValue(record)
    setModalVisible(true)
  }

  const handleDelete = async (id: string) => {
    try {
      await request.delete(`/consumables/${id}`)
      message.success('删除成功')
      fetchData()
    } catch (error) {
      console.error('Delete error:', error)
    }
  }

  const handleAddStock = (consumable_no: string) => {
    setSelectedConsumable(consumable_no)
    stockForm.resetFields()
    setStockModalVisible(true)
  }

  const handleSubmitStock = async (values: any) => {
    try {
      await request.post(`/consumables/${selectedConsumable}/stock/add?quantity=${values.quantity}`)
      message.success('入库成功')
      setStockModalVisible(false)
      fetchData()
    } catch (error) {
      console.error('Add stock error:', error)
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      if (editingItem) {
        await request.put(`/consumables/${editingItem.consumable_no}`, values)
        message.success('更新成功')
      } else {
        await request.post('/consumables', values)
        message.success('添加成功')
      }
      setModalVisible(false)
      fetchData()
    } catch (error) {
      console.error('Submit error:', error)
    }
  }

  const columns = [
    { title: '耗材编号', dataIndex: 'consumable_no', key: 'consumable_no' },
    { title: '耗材名称', dataIndex: 'name', key: 'name' },
    {
      title: '库存数量',
      dataIndex: 'stock_quantity',
      key: 'stock_quantity',
      render: (quantity: number, record: Consumable) => (
        <Space>
          <span>{quantity} {record.unit}</span>
          <Tag color={stockStatusColors[record.stock_status] || 'default'}>
            {record.stock_status}
          </Tag>
        </Space>
      ),
    },
    {
      title: '预警阈值',
      dataIndex: 'warning_threshold',
      key: 'warning_threshold',
      render: (val: number, record: Consumable) => `${val} ${record.unit}`,
    },
    {
      title: '库存状态',
      dataIndex: 'stock_status',
      key: 'stock_status',
      render: (status: string) => (
        <Tag color={stockStatusColors[status] || 'default'}>{status}</Tag>
      ),
    },
    {
      title: '业务状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={businessStatusColors[status] || 'default'}>{status}</Tag>
      ),
    },
    {
      title: '适用服务项目',
      dataIndex: 'applicable_services',
      key: 'applicable_services',
      render: (services: string[]) => services.join(', ') || '-',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Consumable) => (
        <Space size="small">
          <Button
            icon={<InboxOutlined />}
            size="small"
            type="primary"
            onClick={() => handleAddStock(record.consumable_no)}
          >
            入库
          </Button>
          <Button icon={<EditOutlined />} size="small" onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Button
            icon={<DeleteOutlined />}
            size="small"
            danger
            onClick={() => handleDelete(record.consumable_no)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <Card
      title="耗材台账"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          新增耗材
        </Button>
      }
    >
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Input
              placeholder="搜索耗材名称"
              allowClear
              value={filters.name}
              onChange={(e) => setFilters({ ...filters, name: e.target.value })}
            />
          </Col>
          <Col span={8}>
            <Select
              placeholder="选择业务状态"
              allowClear
              style={{ width: '100%' }}
              value={filters.status || undefined}
              onChange={(value) => setFilters({ ...filters, status: value || '' })}
              options={[
                { value: '正常', label: '正常' },
                { value: '停用', label: '停用' },
              ]}
            />
          </Col>
          <Col span={8}>
            <Button onClick={() => setFilters({ name: '', status: '' })}>重置</Button>
          </Col>
        </Row>
      </Card>
      <Table columns={columns} dataSource={data} rowKey="id" loading={loading} />
      <Modal
        title={editingItem ? '编辑耗材' : '新增耗材'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
            name="consumable_no"
            label="耗材编号"
            rules={[{ required: true, message: '请输入耗材编号' }]}
          >
            <Input disabled={!!editingItem} />
          </Form.Item>
          <Form.Item
            name="name"
            label="耗材名称"
            rules={[{ required: true, message: '请输入耗材名称' }]}
          >
            <Input />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="stock_quantity"
                label="库存数量"
                rules={[{ required: true, message: '请输入库存数量' }]}
              >
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="warning_threshold"
                label="预警阈值"
                rules={[{ required: true, message: '请输入预警阈值' }]}
              >
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="unit"
                label="单位"
                rules={[{ required: true, message: '请输入单位' }]}
              >
                <Input placeholder="如: 个、瓶、盒" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="applicable_services" label="适用服务项目">
            <Select
              mode="multiple"
              options={services.map((s) => ({
                value: s.name,
                label: s.name,
              }))}
            />
          </Form.Item>
          <Form.Item name="status" label="业务状态">
            <Select
              options={[
                { value: '正常', label: '正常' },
                { value: '停用', label: '停用' },
              ]}
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              提交
            </Button>
          </Form.Item>
        </Form>
      </Modal>
      <Modal
        title="耗材入库"
        open={stockModalVisible}
        onCancel={() => setStockModalVisible(false)}
        footer={null}
      >
        <Form form={stockForm} layout="vertical" onFinish={handleSubmitStock}>
          <Form.Item
            name="quantity"
            label="入库数量"
            rules={[{ required: true, message: '请输入入库数量' }]}
          >
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              确认入库
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}

export default Consumable
