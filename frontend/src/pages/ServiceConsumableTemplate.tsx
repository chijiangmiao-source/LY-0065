import { useState, useEffect } from 'react'
import { Table, Button, Modal, Form, Input, Select, message, Space, Card, InputNumber, Row, Col, Tag, List } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, MinusCircleOutlined } from '@ant-design/icons'
import request from '../utils/request'

interface TemplateItem {
  consumable_no: string
  consumable_name: string
  quantity: number
  unit: string
}

interface ServiceConsumableTemplate {
  id: string
  template_id: string
  service_id: string
  service_name: string
  items: TemplateItem[]
  remark?: string
  status: string
  created_at: string
}

interface ServiceOption {
  service_id: string
  name: string
  status: string
}

interface ConsumableOption {
  consumable_no: string
  name: string
  unit: string
  stock_quantity: number
  status: string
}

const statusColors: Record<string, string> = {
  '启用': 'green',
  '停用': 'default',
}

const ServiceConsumableTemplatePage = () => {
  const [data, setData] = useState<ServiceConsumableTemplate[]>([])
  const [services, setServices] = useState<ServiceOption[]>([])
  const [consumables, setConsumables] = useState<ConsumableOption[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingItem, setEditingItem] = useState<ServiceConsumableTemplate | null>(null)
  const [form] = Form.useForm()
  const [filters, setFilters] = useState({
    service_name: '',
    status: '',
  })

  const fetchData = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filters.service_name) params.append('service_name', filters.service_name)
      if (filters.status) params.append('status', filters.status)
      const res = await request.get(`/service-consumable-templates?${params.toString()}`) as ServiceConsumableTemplate[]
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

  const fetchConsumables = async () => {
    try {
      const res = await request.get('/consumables') as ConsumableOption[]
      setConsumables(res.filter(c => c.status === '正常'))
    } catch (error) {
      console.error('Fetch consumables error:', error)
    }
  }

  useEffect(() => {
    fetchData()
    fetchServices()
    fetchConsumables()
  }, [filters])

  const handleAdd = () => {
    setEditingItem(null)
    form.resetFields()
    form.setFieldsValue({ items: [] })
    setModalVisible(true)
  }

  const handleEdit = (record: ServiceConsumableTemplate) => {
    setEditingItem(record)
    form.setFieldsValue({
      ...record,
      items: record.items || [],
    })
    setModalVisible(true)
  }

  const handleDelete = async (template_id: string) => {
    try {
      await request.delete(`/service-consumable-templates/${template_id}`)
      message.success('删除成功')
      fetchData()
    } catch (error) {
      console.error('Delete error:', error)
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      if (!values.items || values.items.length === 0) {
        message.error('请至少添加一个耗材')
        return
      }
      const submitData = {
        ...values,
        items: values.items.map((item: any) => {
          const consumable = consumables.find(c => c.consumable_no === item.consumable_no)
          return {
            consumable_no: item.consumable_no,
            consumable_name: consumable?.name || item.consumable_name || '',
            quantity: item.quantity,
            unit: consumable?.unit || item.unit || '个',
          }
        }),
      }
      if (editingItem) {
        await request.put(`/service-consumable-templates/${editingItem.template_id}`, submitData)
        message.success('更新成功')
      } else {
        await request.post('/service-consumable-templates', submitData)
        message.success('添加成功')
      }
      setModalVisible(false)
      fetchData()
    } catch (error) {
      console.error('Submit error:', error)
    }
  }

  const columns = [
    { title: '模板编号', dataIndex: 'template_id', key: 'template_id' },
    { title: '服务编号', dataIndex: 'service_id', key: 'service_id' },
    { title: '服务名称', dataIndex: 'service_name', key: 'service_name' },
    {
      title: '耗材清单',
      dataIndex: 'items',
      key: 'items',
      render: (items: TemplateItem[]) => (
        <List
          size="small"
          dataSource={items}
          renderItem={(item) => (
            <List.Item>
              {item.consumable_name} × {item.quantity} {item.unit}
            </List.Item>
          )}
          style={{ maxWidth: 300 }}
        />
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => <Tag color={statusColors[status] || 'default'}>{status}</Tag>,
    },
    { title: '备注', dataIndex: 'remark', key: 'remark', ellipsis: true },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: ServiceConsumableTemplate) => (
        <Space size="small">
          <Button icon={<EditOutlined />} size="small" onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Button
            icon={<DeleteOutlined />}
            size="small"
            danger
            onClick={() => handleDelete(record.template_id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <Card
      title="服务项目-耗材用量模板"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          新增模板
        </Button>
      }
    >
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Input
              placeholder="搜索服务名称"
              allowClear
              value={filters.service_name}
              onChange={(e) => setFilters({ ...filters, service_name: e.target.value })}
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
                { value: '启用', label: '启用' },
                { value: '停用', label: '停用' },
              ]}
            />
          </Col>
          <Col span={8}>
            <Button onClick={() => setFilters({ service_name: '', status: '' })}>重置</Button>
          </Col>
        </Row>
      </Card>
      <Table columns={columns} dataSource={data} rowKey="id" loading={loading} />
      <Modal
        title={editingItem ? '编辑模板' : '新增模板'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={700}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="template_id"
                label="模板编号"
                rules={[{ required: true, message: '请输入模板编号' }]}
              >
                <Input disabled={!!editingItem} placeholder="如: TPL001" />
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

          <Form.Item label="耗材清单">
            <Form.List name="items">
              {(fields, { add, remove }) => (
                <>
                  {fields.map(({ key, name, ...restField }) => (
                    <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                      <Form.Item
                        {...restField}
                        name={[name, 'consumable_no']}
                        rules={[{ required: true, message: '请选择耗材' }]}
                        style={{ width: 220, marginBottom: 0 }}
                      >
                        <Select
                          placeholder="选择耗材"
                          showSearch
                          optionFilterProp="label"
                          onChange={(value, option) => {
                            const consumable = consumables.find(c => c.consumable_no === value)
                            form.setFields([
                              {
                                name: ['items', name, 'consumable_name'],
                                value: consumable?.name || '',
                              },
                              {
                                name: ['items', name, 'unit'],
                                value: consumable?.unit || '个',
                              },
                            ])
                          }}
                          options={consumables.map((c) => ({
                            value: c.consumable_no,
                            label: `${c.name} (库存: ${c.stock_quantity}${c.unit})`,
                          }))}
                        />
                      </Form.Item>
                      <Form.Item
                        {...restField}
                        name={[name, 'consumable_name']}
                        style={{ display: 'none', marginBottom: 0 }}
                      >
                        <Input />
                      </Form.Item>
                      <Form.Item
                        {...restField}
                        name={[name, 'unit']}
                        style={{ display: 'none', marginBottom: 0 }}
                      >
                        <Input />
                      </Form.Item>
                      <Form.Item
                        {...restField}
                        name={[name, 'quantity']}
                        rules={[{ required: true, message: '请输入用量' }]}
                        style={{ width: 120, marginBottom: 0 }}
                      >
                        <InputNumber min={1} placeholder="用量" style={{ width: '100%' }} />
                      </Form.Item>
                      <MinusCircleOutlined onClick={() => remove(name)} />
                    </Space>
                  ))}
                  <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                    添加耗材
                  </Button>
                </>
              )}
            </Form.List>
          </Form.Item>

          <Form.Item name="status" label="状态">
            <Select
              options={[
                { value: '启用', label: '启用' },
                { value: '停用', label: '停用' },
              ]}
            />
          </Form.Item>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={2} />
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

export default ServiceConsumableTemplatePage
