import { useState, useEffect } from 'react'
import { Table, Button, Modal, Form, Input, Select, message, Space, Card, InputNumber } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import request from '../utils/request'

interface Service {
  id: string
  service_id: string
  name: string
  duration: number
  price: number
  description: string
  status: string
  created_at: string
}

const Service = () => {
  const [data, setData] = useState<Service[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingItem, setEditingItem] = useState<Service | null>(null)
  const [form] = Form.useForm()

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await request.get('/services') as Service[]
      setData(res)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleAdd = () => {
    setEditingItem(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record: Service) => {
    setEditingItem(record)
    form.setFieldsValue(record)
    setModalVisible(true)
  }

  const handleDelete = async (id: string) => {
    try {
      await request.delete(`/services/${id}`)
      message.success('删除成功')
      fetchData()
    } catch (error) {
      console.error('Delete error:', error)
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      if (editingItem) {
        await request.put(`/services/${editingItem.service_id}`, values)
        message.success('更新成功')
      } else {
        await request.post('/services', values)
        message.success('添加成功')
      }
      setModalVisible(false)
      fetchData()
    } catch (error) {
      console.error('Submit error:', error)
    }
  }

  const columns = [
    { title: '服务编号', dataIndex: 'service_id', key: 'service_id' },
    { title: '服务名称', dataIndex: 'name', key: 'name' },
    { title: '时长(分钟)', dataIndex: 'duration', key: 'duration' },
    { title: '价格(元)', dataIndex: 'price', key: 'price' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Select
          value={status}
          style={{ width: 100 }}
          disabled
          options={[
            { value: '启用', label: '启用' },
            { value: '停用', label: '停用' },
          ]}
        />
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Service) => (
        <Space>
          <Button icon={<EditOutlined />} size="small" onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Button
            icon={<DeleteOutlined />}
            size="small"
            danger
            onClick={() => handleDelete(record.service_id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <Card
      title="服务项目管理"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          新增服务
        </Button>
      }
    >
      <Table columns={columns} dataSource={data} rowKey="id" loading={loading} />
      <Modal
        title={editingItem ? '编辑服务' : '新增服务'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
            name="service_id"
            label="服务编号"
            rules={[{ required: true, message: '请输入服务编号' }]}
          >
            <Input disabled={!!editingItem} />
          </Form.Item>
          <Form.Item
            name="name"
            label="服务名称"
            rules={[{ required: true, message: '请输入服务名称' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="duration"
            label="服务时长(分钟)"
            rules={[{ required: true, message: '请输入服务时长' }]}
          >
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="price"
            label="服务价格(元)"
            rules={[{ required: true, message: '请输入服务价格' }]}
          >
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="description" label="服务描述">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="status" label="状态">
            <Select
              options={[
                { value: '启用', label: '启用' },
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
    </Card>
  )
}

export default Service
