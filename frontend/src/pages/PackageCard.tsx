import { useState, useEffect } from 'react'
import {
  Table, Button, Modal, Form, Input, Select, message, Space, Card, Row, Col, Tag,
  Tabs, InputNumber, List, Alert, Descriptions, Statistic, Divider, Checkbox
} from 'antd'
import {
  PlusOutlined, EditOutlined, DeleteOutlined, GiftOutlined,
  CreditCardOutlined, HistoryOutlined, CheckCircleOutlined,
  PauseCircleOutlined, StopOutlined, PlayCircleOutlined, ThunderboltOutlined
} from '@ant-design/icons'
import request from '../utils/request'

interface PackageCard {
  id: string
  package_no: string
  name: string
  package_type: string
  price: number
  total_times: number
  gift_times: number
  valid_days: number
  applicable_service_ids: string[]
  applicable_service_names: string[]
  applicable_employee_ids: string[]
  applicable_store_ids: string[]
  allow_mixed_payment: boolean
  description?: string
  status: string
  created_at: string
}

interface MemberPackage {
  id: string
  member_package_no: string
  member_no: string
  member_name: string
  phone: string
  package_no: string
  package_name: string
  package_type: string
  total_times: number
  used_times: number
  remaining_times: number
  price: number
  purchase_date: string
  expire_date: string
  applicable_service_ids: string[]
  applicable_service_names: string[]
  applicable_employee_ids: string[]
  allow_mixed_payment: boolean
  status: string
  operator: string
  remark?: string
  created_at: string
}

interface PackageRedemption {
  id: string
  redemption_no: string
  member_package_no: string
  member_no: string
  member_name: string
  phone: string
  package_no: string
  package_name: string
  appointment_no?: string
  service_id: string
  service_name: string
  employee_id?: string
  employee_name?: string
  redeem_times: number
  remaining_before: number
  remaining_after: number
  mixed_payment: boolean
  mixed_pay_amount?: number
  operator: string
  remark?: string
  created_at: string
}

interface ServiceOption {
  service_id: string
  name: string
  price: number
  status: string
}

interface MemberOption {
  member_no: string
  name: string
  phone: string
  level_name: string
  balance: number
  status: string
}

const statusColors: Record<string, string> = {
  '启用': 'green',
  '禁用': 'default',
  '生效中': 'green',
  '已冻结': 'orange',
  '已过期': 'red',
  '已作废': 'default',
}

const PackageCardPage = () => {
  const [activeTab, setActiveTab] = useState('packages')

  const [packages, setPackages] = useState<PackageCard[]>([])
  const [memberPackages, setMemberPackages] = useState<MemberPackage[]>([])
  const [redemptions, setRedemptions] = useState<PackageRedemption[]>([])
  const [services, setServices] = useState<ServiceOption[]>([])
  const [members, setMembers] = useState<MemberOption[]>([])

  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [activateModalVisible, setActivateModalVisible] = useState(false)
  const [renewModalVisible, setRenewModalVisible] = useState(false)
  const [statusModalVisible, setStatusModalVisible] = useState(false)

  const [editingPackage, setEditingPackage] = useState<PackageCard | null>(null)
  const [renewingMemberPackage, setRenewingMemberPackage] = useState<MemberPackage | null>(null)
  const [statusMemberPackage, setStatusMemberPackage] = useState<MemberPackage | null>(null)
  const [targetStatus, setTargetStatus] = useState<string>('')

  const [packageForm] = Form.useForm()
  const [activateForm] = Form.useForm()
  const [renewForm] = Form.useForm()
  const [statusForm] = Form.useForm()

  const [packageFilters, setPackageFilters] = useState({ name: '', status: '', package_type: '' })
  const [memberPackageFilters, setMemberPackageFilters] = useState({ member_no: '', status: '' })
  const [redemptionFilters, setRedemptionFilters] = useState({ member_no: '' })

  const fetchPackages = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (packageFilters.name) params.append('name', packageFilters.name)
      if (packageFilters.status) params.append('status', packageFilters.status)
      if (packageFilters.package_type) params.append('package_type', packageFilters.package_type)
      const res = await request.get(`/package-cards?${params.toString()}`) as PackageCard[]
      setPackages(res)
    } finally {
      setLoading(false)
    }
  }

  const fetchMemberPackages = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (memberPackageFilters.member_no) params.append('member_no', memberPackageFilters.member_no)
      if (memberPackageFilters.status) params.append('status', memberPackageFilters.status)
      const res = await request.get(`/package-cards/member/list?${params.toString()}`) as MemberPackage[]
      setMemberPackages(res)
    } finally {
      setLoading(false)
    }
  }

  const fetchRedemptions = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (redemptionFilters.member_no) params.append('member_no', redemptionFilters.member_no)
      const res = await request.get(`/package-cards/redemptions?${params.toString()}`) as PackageRedemption[]
      setRedemptions(res)
    } finally {
      setLoading(false)
    }
  }

  const fetchServices = async () => {
    try {
      const res = await request.get('/services') as ServiceOption[]
      setServices(res.filter(s => s.status === '启用'))
    } catch (error) {
      console.error(error)
    }
  }

  const fetchMembers = async () => {
    try {
      const res = await request.get('/members') as MemberOption[]
      setMembers(res.filter(m => m.status === '正常'))
    } catch (error) {
      console.error(error)
    }
  }

  useEffect(() => {
    if (activeTab === 'packages') fetchPackages()
    else if (activeTab === 'member-packages') fetchMemberPackages()
    else if (activeTab === 'redemptions') fetchRedemptions()
  }, [activeTab])

  useEffect(() => {
    fetchServices()
    fetchMembers()
  }, [])

  const handleAddPackage = () => {
    setEditingPackage(null)
    packageForm.resetFields()
    packageForm.setFieldsValue({
      package_type: '次卡',
      price: 0,
      total_times: 10,
      gift_times: 0,
      valid_days: 365,
      allow_mixed_payment: true,
      applicable_service_ids: [],
      status: '启用'
    })
    setModalVisible(true)
  }

  const handleEditPackage = (record: PackageCard) => {
    setEditingPackage(record)
    packageForm.setFieldsValue({
      ...record,
      applicable_service_ids: record.applicable_service_ids
    })
    setModalVisible(true)
  }

  const handleDeletePackage = async (package_no: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '删除后无法恢复，确认删除该套餐吗？',
      onOk: async () => {
        try {
          await request.delete(`/package-cards/${package_no}`)
          message.success('删除成功')
          fetchPackages()
        } catch (error) {
          console.error(error)
        }
      },
    })
  }

  const handlePackageSubmit = async (values: any) => {
    try {
      const selectedServices = services.filter(s => values.applicable_service_ids?.includes(s.service_id))
      const payload = {
        ...values,
        applicable_service_names: selectedServices.map(s => s.name)
      }
      if (editingPackage) {
        await request.put(`/package-cards/${editingPackage.package_no}`, payload)
        message.success('更新成功')
      } else {
        await request.post('/package-cards', payload)
        message.success('添加成功')
      }
      setModalVisible(false)
      fetchPackages()
    } catch (error) {
      console.error(error)
    }
  }

  const handleActivate = () => {
    activateForm.resetFields()
    setActivateModalVisible(true)
  }

  const handleActivateSubmit = async (values: any) => {
    try {
      await request.post('/package-cards/member/activate', values)
      message.success('套餐开通成功')
      setActivateModalVisible(false)
      fetchMemberPackages()
    } catch (error) {
      console.error(error)
    }
  }

  const handleRenew = (record: MemberPackage) => {
    setRenewingMemberPackage(record)
    renewForm.resetFields()
    setRenewModalVisible(true)
  }

  const handleRenewSubmit = async (values: any) => {
    if (!renewingMemberPackage) return
    try {
      await request.post('/package-cards/member/renew', {
        member_package_no: renewingMemberPackage.member_package_no,
        ...values
      })
      message.success('续费成功')
      setRenewModalVisible(false)
      fetchMemberPackages()
    } catch (error) {
      console.error(error)
    }
  }

  const handleStatusChange = (record: MemberPackage, status: string) => {
    setStatusMemberPackage(record)
    setTargetStatus(status)
    statusForm.resetFields()
    setStatusModalVisible(true)
  }

  const handleStatusSubmit = async (values: any) => {
    if (!statusMemberPackage) return
    try {
      await request.post(`/package-cards/member/${statusMemberPackage.member_package_no}/status`, {
        status: targetStatus,
        ...values
      })
      message.success('状态更新成功')
      setStatusModalVisible(false)
      fetchMemberPackages()
    } catch (error) {
      console.error(error)
    }
  }

  const packageColumns = [
    { title: '套餐编号', dataIndex: 'package_no', key: 'package_no' },
    { title: '套餐名称', dataIndex: 'name', key: 'name' },
    { title: '类型', dataIndex: 'package_type', key: 'package_type',
      render: (t: string) => <Tag color="purple">{t}</Tag>
    },
    { title: '价格', dataIndex: 'price', key: 'price',
      render: (val: number) => <span style={{ fontWeight: 600, color: '#f5222d' }}>¥{val.toFixed(2)}</span>
    },
    { title: '总次数', key: 'times',
      render: (_: any, record: PackageCard) => (
        <Space>
          <span>{record.total_times}次</span>
          {record.gift_times > 0 && <Tag color="orange">赠送{record.gift_times}次</Tag>}
        </Space>
      )
    },
    { title: '有效期', dataIndex: 'valid_days', key: 'valid_days',
      render: (val: number) => <span>{val}天</span>
    },
    { title: '适用服务', key: 'services',
      render: (_: any, record: PackageCard) => (
        record.applicable_service_names.length > 0
          ? <Space wrap>{record.applicable_service_names.map(s => <Tag key={s} color="blue">{s}</Tag>)}</Space>
          : <Tag color="default">全部服务</Tag>
      )
    },
    { title: '混合支付', dataIndex: 'allow_mixed_payment', key: 'allow_mixed_payment',
      render: (val: boolean) => val ? <Tag color="green">允许</Tag> : <Tag color="red">不允许</Tag>
    },
    { title: '状态', dataIndex: 'status', key: 'status',
      render: (status: string) => <Tag color={statusColors[status] || 'default'}>{status}</Tag>
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: PackageCard) => (
        <Space size="small">
          <Button icon={<EditOutlined />} size="small" onClick={() => handleEditPackage(record)}>编辑</Button>
          <Button icon={<DeleteOutlined />} size="small" danger onClick={() => handleDeletePackage(record.package_no)}>删除</Button>
        </Space>
      ),
    },
  ]

  const memberPackageColumns = [
    { title: '会员套餐编号', dataIndex: 'member_package_no', key: 'member_package_no' },
    { title: '会员姓名', dataIndex: 'member_name', key: 'member_name' },
    { title: '联系电话', dataIndex: 'phone', key: 'phone' },
    { title: '套餐名称', dataIndex: 'package_name', key: 'package_name' },
    { title: '总次数', dataIndex: 'total_times', key: 'total_times' },
    { title: '已使用', dataIndex: 'used_times', key: 'used_times' },
    { title: '剩余次数', dataIndex: 'remaining_times', key: 'remaining_times',
      render: (val: number) => (
        <span style={{
          color: val <= 3 ? '#f5222d' : '#52c41a',
          fontWeight: 600
        }}>{val}次</span>
      )
    },
    { title: '购买日期', dataIndex: 'purchase_date', key: 'purchase_date',
      render: (val: string) => new Date(val).toLocaleDateString()
    },
    { title: '过期日期', dataIndex: 'expire_date', key: 'expire_date',
      render: (val: string) => {
        const expire = new Date(val)
        const now = new Date()
        const diffDays = Math.ceil((expire.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
        return (
          <Space>
            <span>{expire.toLocaleDateString()}</span>
            {diffDays <= 7 && diffDays > 0 && <Tag color="orange">还有{diffDays}天</Tag>}
            {diffDays <= 0 && <Tag color="red">已过期</Tag>}
          </Space>
        )
      }
    },
    { title: '状态', dataIndex: 'status', key: 'status',
      render: (status: string) => <Tag color={statusColors[status] || 'default'}>{status}</Tag>
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: MemberPackage) => (
        <Space size="small" wrap>
          <Button icon={<GiftOutlined />} size="small" type="primary" onClick={() => handleRenew(record)}>续费</Button>
          {record.status === '生效中' && (
            <Button icon={<PauseCircleOutlined />} size="small" onClick={() => handleStatusChange(record, '已冻结')}>冻结</Button>
          )}
          {record.status === '已冻结' && (
            <Button icon={<PlayCircleOutlined />} size="small" type="primary" onClick={() => handleStatusChange(record, '生效中')}>解冻</Button>
          )}
          {record.status !== '已作废' && (
            <Button icon={<StopOutlined />} size="small" danger onClick={() => handleStatusChange(record, '已作废')}>作废</Button>
          )}
        </Space>
      ),
    },
  ]

  const redemptionColumns = [
    { title: '核销编号', dataIndex: 'redemption_no', key: 'redemption_no' },
    { title: '会员姓名', dataIndex: 'member_name', key: 'member_name' },
    { title: '联系电话', dataIndex: 'phone', key: 'phone' },
    { title: '套餐名称', dataIndex: 'package_name', key: 'package_name' },
    { title: '服务项目', dataIndex: 'service_name', key: 'service_name' },
    { title: '服务员工', dataIndex: 'employee_name', key: 'employee_name' },
    { title: '核销次数', dataIndex: 'redeem_times', key: 'redeem_times' },
    { title: '核销前剩余', dataIndex: 'remaining_before', key: 'remaining_before' },
    { title: '核销后剩余', dataIndex: 'remaining_after', key: 'remaining_after' },
    { title: '混合支付', dataIndex: 'mixed_payment', key: 'mixed_payment',
      render: (val: boolean, record: PackageRedemption) => val
        ? <Tag color="orange">是 ¥{record.mixed_pay_amount?.toFixed(2)}</Tag>
        : <Tag color="default">否</Tag>
    },
    { title: '关联预约', dataIndex: 'appointment_no', key: 'appointment_no' },
    { title: '操作人', dataIndex: 'operator', key: 'operator' },
    { title: '核销时间', dataIndex: 'created_at', key: 'created_at',
      render: (val: string) => new Date(val).toLocaleString()
    },
  ]

  const totalPackageCount = packages.length
  const totalMemberPackageCount = memberPackages.length
  const activeMemberPackageCount = memberPackages.filter(mp => mp.status === '生效中').length
  const totalRemainingTimes = memberPackages.reduce((sum, mp) => sum + mp.remaining_times, 0)

  const statusActionText: Record<string, string> = {
    '生效中': '解冻',
    '已冻结': '冻结',
    '已作废': '作废'
  }

  const tabItems = [
    {
      key: 'packages',
      label: <span><CreditCardOutlined />套餐规则</span>,
      children: (
        <Card
          extra={
            <Space>
              <Button type="primary" icon={<PlusOutlined />} onClick={handleAddPackage}>新增套餐</Button>
              <Button onClick={fetchPackages}>刷新</Button>
            </Space>
          }
        >
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Statistic title="套餐总数" value={totalPackageCount} prefix={<CreditCardOutlined />} />
            </Col>
            <Col span={6}>
              <Statistic title="启用套餐" value={packages.filter(p => p.status === '启用').length} valueStyle={{ color: '#52c41a' }} />
            </Col>
            <Col span={6}>
              <Statistic title="会员套餐数" value={totalMemberPackageCount} prefix={<GiftOutlined />} />
            </Col>
            <Col span={6}>
              <Statistic title="生效中套餐剩余总次数" value={totalRemainingTimes} suffix="次" valueStyle={{ color: '#1890ff' }} />
            </Col>
          </Row>
          <Card size="small" style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col span={8}>
                <Input
                  placeholder="搜索套餐名称"
                  allowClear
                  value={packageFilters.name}
                  onChange={(e) => setPackageFilters({ ...packageFilters, name: e.target.value })}
                  onPressEnter={fetchPackages}
                />
              </Col>
              <Col span={8}>
                <Select
                  placeholder="套餐类型"
                  allowClear
                  style={{ width: '100%' }}
                  value={packageFilters.package_type || undefined}
                  onChange={(value) => setPackageFilters({ ...packageFilters, package_type: value || '' })}
                  options={[{ value: '次卡', label: '次卡' }, { value: '套餐', label: '套餐' }]}
                />
              </Col>
              <Col span={8}>
                <Space>
                  <Select
                    placeholder="状态"
                    allowClear
                    style={{ width: 120 }}
                    value={packageFilters.status || undefined}
                    onChange={(value) => setPackageFilters({ ...packageFilters, status: value || '' })}
                    options={[{ value: '启用', label: '启用' }, { value: '禁用', label: '禁用' }]}
                  />
                  <Button onClick={fetchPackages} type="primary">查询</Button>
                  <Button onClick={() => {
                    setPackageFilters({ name: '', status: '', package_type: '' })
                    fetchPackages()
                  }}>重置</Button>
                </Space>
              </Col>
            </Row>
          </Card>
          <Table columns={packageColumns} dataSource={packages} rowKey="id" loading={loading} />
        </Card>
      ),
    },
    {
      key: 'member-packages',
      label: <span><GiftOutlined />会员套餐</span>,
      children: (
        <Card
          extra={
            <Space>
              <Button type="primary" icon={<ThunderboltOutlined />} onClick={handleActivate}>开通套餐</Button>
              <Button onClick={fetchMemberPackages}>刷新</Button>
            </Space>
          }
        >
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Statistic title="会员套餐总数" value={totalMemberPackageCount} prefix={<GiftOutlined />} />
            </Col>
            <Col span={6}>
              <Statistic title="生效中" value={activeMemberPackageCount} valueStyle={{ color: '#52c41a' }} />
            </Col>
            <Col span={6}>
              <Statistic title="已冻结" value={memberPackages.filter(mp => mp.status === '已冻结').length} valueStyle={{ color: '#faad14' }} />
            </Col>
            <Col span={6}>
              <Statistic title="已过期/作废" value={memberPackages.filter(mp => ['已过期', '已作废'].includes(mp.status)).length} valueStyle={{ color: '#ff4d4f' }} />
            </Col>
          </Row>
          <Card size="small" style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col span={12}>
                <Input
                  placeholder="搜索会员编号"
                  allowClear
                  value={memberPackageFilters.member_no}
                  onChange={(e) => setMemberPackageFilters({ ...memberPackageFilters, member_no: e.target.value })}
                  onPressEnter={fetchMemberPackages}
                />
              </Col>
              <Col span={12}>
                <Space>
                  <Select
                    placeholder="状态"
                    allowClear
                    style={{ width: 160 }}
                    value={memberPackageFilters.status || undefined}
                    onChange={(value) => setMemberPackageFilters({ ...memberPackageFilters, status: value || '' })}
                    options={[
                      { value: '生效中', label: '生效中' },
                      { value: '已冻结', label: '已冻结' },
                      { value: '已过期', label: '已过期' },
                      { value: '已作废', label: '已作废' }
                    ]}
                  />
                  <Button onClick={fetchMemberPackages} type="primary">查询</Button>
                  <Button onClick={() => {
                    setMemberPackageFilters({ member_no: '', status: '' })
                    fetchMemberPackages()
                  }}>重置</Button>
                </Space>
              </Col>
            </Row>
          </Card>
          <Table columns={memberPackageColumns} dataSource={memberPackages} rowKey="id" loading={loading} />
        </Card>
      ),
    },
    {
      key: 'redemptions',
      label: <span><HistoryOutlined />核销记录</span>,
      children: (
        <Card
          extra={
            <Space>
              <Input
                placeholder="搜索会员编号"
                allowClear
                style={{ width: 200 }}
                value={redemptionFilters.member_no}
                onChange={(e) => setRedemptionFilters({ ...redemptionFilters, member_no: e.target.value })}
                onPressEnter={fetchRedemptions}
              />
              <Button type="primary" onClick={fetchRedemptions}>查询</Button>
              <Button onClick={() => {
                setRedemptionFilters({ member_no: '' })
                fetchRedemptions()
              }}>重置</Button>
            </Space>
          }
        >
          <Alert
            type="info"
            showIcon
            message={`共 ${redemptions.length} 条核销记录`}
            style={{ marginBottom: 16 }}
          />
          <Table columns={redemptionColumns} dataSource={redemptions} rowKey="id" loading={loading} />
        </Card>
      ),
    },
  ]

  return (
    <Card title="会员套餐与次卡管理">
      <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />

      <Modal
        title={editingPackage ? '编辑套餐' : '新增套餐'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={720}
      >
        <Form form={packageForm} layout="vertical" onFinish={handlePackageSubmit}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="package_no"
                label="套餐编号"
              >
                <Input disabled placeholder="留空自动生成" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="name"
                label="套餐名称"
                rules={[{ required: true, message: '请输入套餐名称' }]}
              >
                <Input placeholder="如：洗剪吹10次卡" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="package_type"
                label="套餐类型"
                rules={[{ required: true, message: '请选择套餐类型' }]}
              >
                <Select options={[{ value: '次卡', label: '次卡' }, { value: '套餐', label: '套餐' }]} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="price"
                label="套餐价格(元)"
                rules={[{ required: true, message: '请输入套餐价格' }]}
              >
                <InputNumber style={{ width: '100%' }} min={0} precision={2} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="total_times"
                label="购买次数"
                rules={[{ required: true, message: '请输入购买次数' }]}
              >
                <InputNumber style={{ width: '100%' }} min={1} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="gift_times"
                label="赠送次数"
              >
                <InputNumber style={{ width: '100%' }} min={0} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="valid_days"
                label="有效期(天)"
                rules={[{ required: true, message: '请输入有效期' }]}
              >
                <InputNumber style={{ width: '100%' }} min={1} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item
            name="applicable_service_ids"
            label="适用服务项目（不选表示全部适用）"
          >
            <Checkbox.Group style={{ width: '100%' }}>
              <Row>
                {services.map(s => (
                  <Col span={8} key={s.service_id}>
                    <Checkbox value={s.service_id}>{s.name} (¥{s.price})</Checkbox>
                  </Col>
                ))}
              </Row>
            </Checkbox.Group>
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="allow_mixed_payment"
                label="是否允许与余额混合支付"
                valuePropName="checked"
              >
                <Select
                  options={[
                    { value: true, label: '允许' },
                    { value: false, label: '不允许' }
                  ]}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="status"
                label="状态"
              >
                <Select options={[{ value: '启用', label: '启用' }, { value: '禁用', label: '禁用' }]} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="description" label="套餐描述">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>提交</Button>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="为会员开通套餐"
        open={activateModalVisible}
        onCancel={() => setActivateModalVisible(false)}
        footer={null}
        width={520}
      >
        <Form form={activateForm} layout="vertical" onFinish={handleActivateSubmit}>
          <Form.Item
            name="member_no"
            label="选择会员"
            rules={[{ required: true, message: '请选择会员' }]}
          >
            <Select
              showSearch
              placeholder="搜索会员编号/姓名"
              optionFilterProp="children"
              options={members.map(m => ({
                value: m.member_no,
                label: `${m.member_no} - ${m.name} (${m.phone})`
              }))}
            />
          </Form.Item>
          <Form.Item
            name="package_no"
            label="选择套餐"
            rules={[{ required: true, message: '请选择套餐' }]}
          >
            <Select
              showSearch
              placeholder="搜索套餐"
              optionFilterProp="children"
              options={packages.filter(p => p.status === '启用').map(p => ({
                value: p.package_no,
                label: `${p.name} - ¥${p.price} (${p.total_times + p.gift_times}次/${p.valid_days}天)`
              }))}
            />
          </Form.Item>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>确认开通</Button>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`续费套餐 - ${renewingMemberPackage?.package_name || ''}`}
        open={renewModalVisible}
        onCancel={() => setRenewModalVisible(false)}
        footer={null}
        width={520}
      >
        {renewingMemberPackage && (
          <>
            <Descriptions size="small" column={1} bordered style={{ marginBottom: 16 }}>
              <Descriptions.Item label="会员">{renewingMemberPackage.member_name}</Descriptions.Item>
              <Descriptions.Item label="当前剩余次数">{renewingMemberPackage.remaining_times}次</Descriptions.Item>
              <Descriptions.Item label="当前过期日期">{new Date(renewingMemberPackage.expire_date).toLocaleDateString()}</Descriptions.Item>
            </Descriptions>
            <Alert
              type="info"
              showIcon
              message="续费将按照原套餐规则增加次数和延长有效期"
              style={{ marginBottom: 16 }}
            />
            <Form form={renewForm} layout="vertical" onFinish={handleRenewSubmit}>
              <Form.Item name="remark" label="备注">
                <Input.TextArea rows={2} />
              </Form.Item>
              <Form.Item>
                <Button type="primary" htmlType="submit" block>确认续费</Button>
              </Form.Item>
            </Form>
          </>
        )}
      </Modal>

      <Modal
        title={`${statusActionText[targetStatus] || '状态变更'}套餐`}
        open={statusModalVisible}
        onCancel={() => setStatusModalVisible(false)}
        footer={null}
        width={520}
      >
        {statusMemberPackage && (
          <>
            <Descriptions size="small" column={1} bordered style={{ marginBottom: 16 }}>
              <Descriptions.Item label="会员">{statusMemberPackage.member_name}</Descriptions.Item>
              <Descriptions.Item label="套餐">{statusMemberPackage.package_name}</Descriptions.Item>
              <Descriptions.Item label="当前状态">
                <Tag color={statusColors[statusMemberPackage.status]}>{statusMemberPackage.status}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="目标状态">
                <Tag color={statusColors[targetStatus]}>{targetStatus}</Tag>
              </Descriptions.Item>
            </Descriptions>
            {targetStatus === '已作废' && (
              <Alert
                type="warning"
                showIcon
                message="作废操作不可恢复，请谨慎操作"
                style={{ marginBottom: 16 }}
              />
            )}
            <Form form={statusForm} layout="vertical" onFinish={handleStatusSubmit}>
              <Form.Item name="remark" label="变更原因/备注">
                <Input.TextArea rows={2} />
              </Form.Item>
              <Form.Item>
                <Button type="primary" htmlType="submit" block danger={targetStatus === '已作废'}>
                  确认{statusActionText[targetStatus] || '变更'}
                </Button>
              </Form.Item>
            </Form>
          </>
        )}
      </Modal>
    </Card>
  )
}

export default PackageCardPage
