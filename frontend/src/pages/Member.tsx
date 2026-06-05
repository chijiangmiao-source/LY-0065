import { useState, useEffect } from 'react'
import {
  Table, Button, Modal, Form, Input, Select, message, Space, Card, Row, Col, Tag,
  Tabs, Statistic, InputNumber, Divider, Descriptions, List
} from 'antd'
import {
  PlusOutlined, EditOutlined, DeleteOutlined, WalletOutlined, HistoryOutlined,
  CrownOutlined, UserOutlined, ReloadOutlined
} from '@ant-design/icons'
import request from '../utils/request'

interface MemberLevel {
  id: string
  level_id: string
  name: string
  min_recharge: number
  discount_rate: number
  description?: string
  status: string
  created_at: string
}

interface Member {
  id: string
  member_no: string
  name: string
  phone: string
  gender?: string
  level_id: string
  level_name: string
  balance: number
  total_recharge: number
  total_consumption: number
  remark?: string
  status: string
  created_at: string
}

interface MemberRecharge {
  id: string
  recharge_no: string
  member_no: string
  member_name: string
  phone: string
  recharge_amount: number
  gift_amount: number
  total_amount: number
  balance_before: number
  balance_after: number
  operator: string
  remark?: string
  created_at: string
}

interface MemberConsumption {
  id: string
  consumption_no: string
  member_no?: string
  member_name?: string
  phone?: string
  appointment_no?: string
  service_id: string
  service_name: string
  original_price: number
  discount_rate: number
  actual_amount: number
  pay_method: string
  balance_before?: number
  balance_after?: number
  operator: string
  remark?: string
  created_at: string
}

interface OperationLog {
  id: string
  log_id: string
  operator: string
  module: string
  action: string
  target_id?: string
  detail?: string
  created_at: string
}

const MemberPage = () => {
  const [activeTab, setActiveTab] = useState('members')

  const [members, setMembers] = useState<Member[]>([])
  const [levels, setLevels] = useState<MemberLevel[]>([])
  const [recharges, setRecharges] = useState<MemberRecharge[]>([])
  const [consumptions, setConsumptions] = useState<MemberConsumption[]>([])
  const [logs, setLogs] = useState<OperationLog[]>([])

  const [loading, setLoading] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)

  const [memberModalVisible, setMemberModalVisible] = useState(false)
  const [levelModalVisible, setLevelModalVisible] = useState(false)
  const [rechargeModalVisible, setRechargeModalVisible] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)

  const [editingMember, setEditingMember] = useState<Member | null>(null)
  const [editingLevel, setEditingLevel] = useState<MemberLevel | null>(null)
  const [rechargingMember, setRechargingMember] = useState<Member | null>(null)
  const [detailMember, setDetailMember] = useState<Member | null>(null)

  const [memberForm] = Form.useForm()
  const [levelForm] = Form.useForm()
  const [rechargeForm] = Form.useForm()

  const [memberFilters, setMemberFilters] = useState({ name: '', phone: '', level_id: '', status: '' })
  const [levelFilters, setLevelFilters] = useState({ status: '' })
  const [consumptionFilters, setConsumptionFilters] = useState({ pay_method: '' })
  const [logFilters, setLogFilters] = useState({ module: '', operator: '' })

  const fetchMembers = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (memberFilters.name) params.append('name', memberFilters.name)
      if (memberFilters.phone) params.append('phone', memberFilters.phone)
      if (memberFilters.level_id) params.append('level_id', memberFilters.level_id)
      if (memberFilters.status) params.append('status', memberFilters.status)
      const res = await request.get(`/members?${params.toString()}`) as Member[]
      setMembers(res)
    } finally {
      setLoading(false)
    }
  }

  const fetchLevels = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (levelFilters.status) params.append('status', levelFilters.status)
      const res = await request.get(`/members/levels?${params.toString()}`) as MemberLevel[]
      setLevels(res)
    } finally {
      setLoading(false)
    }
  }

  const fetchConsumptions = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (consumptionFilters.pay_method) params.append('pay_method', consumptionFilters.pay_method)
      const res = await request.get(`/members/consumptions/all?${params.toString()}`) as MemberConsumption[]
      setConsumptions(res)
    } finally {
      setLoading(false)
    }
  }

  const fetchLogs = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (logFilters.module) params.append('module', logFilters.module)
      if (logFilters.operator) params.append('operator', logFilters.operator)
      const res = await request.get(`/members/logs/all?${params.toString()}`) as OperationLog[]
      setLogs(res)
    } finally {
      setLoading(false)
    }
  }

  const fetchMemberDetail = async (member_no: string) => {
    setDetailLoading(true)
    try {
      const [rechargeRes, consumptionRes] = await Promise.all([
        request.get(`/members/${member_no}/recharges`) as Promise<MemberRecharge[]>,
        request.get(`/members/${member_no}/consumptions`) as Promise<MemberConsumption[]>,
      ])
      setRecharges(rechargeRes)
      setConsumptions(consumptionRes)
    } finally {
      setDetailLoading(false)
    }
  }

  useEffect(() => {
    if (activeTab === 'members') fetchMembers()
    else if (activeTab === 'levels') fetchLevels()
    else if (activeTab === 'consumptions') fetchConsumptions()
    else if (activeTab === 'logs') fetchLogs()
  }, [activeTab])

  useEffect(() => {
    if (activeTab === 'levels') fetchLevels()
  }, [])

  const handleAddMember = () => {
    setEditingMember(null)
    memberForm.resetFields()
    setMemberModalVisible(true)
  }

  const handleEditMember = (record: Member) => {
    setEditingMember(record)
    memberForm.setFieldsValue(record)
    setMemberModalVisible(true)
  }

  const handleDeleteMember = async (member_no: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '删除后无法恢复，确认删除该会员吗？',
      onOk: async () => {
        try {
          await request.delete(`/members/${member_no}`)
          message.success('删除成功')
          fetchMembers()
        } catch (error) {
          console.error(error)
        }
      },
    })
  }

  const handleRecharge = (record: Member) => {
    setRechargingMember(record)
    rechargeForm.resetFields()
    rechargeForm.setFieldsValue({ recharge_amount: 0, gift_amount: 0 })
    setRechargeModalVisible(true)
  }

  const handleViewDetail = (record: Member) => {
    setDetailMember(record)
    setDetailModalVisible(true)
    fetchMemberDetail(record.member_no)
  }

  const handleMemberSubmit = async (values: any) => {
    try {
      if (editingMember) {
        await request.put(`/members/${editingMember.member_no}`, values)
        message.success('更新成功')
      } else {
        await request.post('/members', values)
        message.success('添加成功')
      }
      setMemberModalVisible(false)
      fetchMembers()
    } catch (error) {
      console.error(error)
    }
  }

  const handleRechargeSubmit = async (values: any) => {
    if (!rechargingMember) return
    try {
      await request.post(`/members/${rechargingMember.member_no}/recharge`, values)
      message.success('充值成功')
      setRechargeModalVisible(false)
      fetchMembers()
      if (detailMember && detailMember.member_no === rechargingMember.member_no) {
        fetchMemberDetail(detailMember.member_no)
      }
    } catch (error) {
      console.error(error)
    }
  }

  const handleAddLevel = () => {
    setEditingLevel(null)
    levelForm.resetFields()
    levelForm.setFieldsValue({ discount_rate: 1.0, min_recharge: 0 })
    setLevelModalVisible(true)
  }

  const handleEditLevel = (record: MemberLevel) => {
    setEditingLevel(record)
    levelForm.setFieldsValue(record)
    setLevelModalVisible(true)
  }

  const handleDeleteLevel = async (level_id: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '删除后无法恢复，确认删除该会员等级吗？',
      onOk: async () => {
        try {
          await request.delete(`/members/levels/${level_id}`)
          message.success('删除成功')
          fetchLevels()
        } catch (error) {
          console.error(error)
        }
      },
    })
  }

  const handleLevelSubmit = async (values: any) => {
    try {
      if (editingLevel) {
        await request.put(`/members/levels/${editingLevel.level_id}`, values)
        message.success('更新成功')
      } else {
        await request.post('/members/levels', values)
        message.success('添加成功')
      }
      setLevelModalVisible(false)
      fetchLevels()
    } catch (error) {
      console.error(error)
    }
  }

  const memberColumns = [
    { title: '会员编号', dataIndex: 'member_no', key: 'member_no' },
    { title: '姓名', dataIndex: 'name', key: 'name' },
    { title: '联系电话', dataIndex: 'phone', key: 'phone' },
    { title: '性别', dataIndex: 'gender', key: 'gender' },
    { title: '会员等级', dataIndex: 'level_name', key: 'level_name',
      render: (name: string, record: Member) => {
        const level = levels.find(l => l.level_id === record.level_id)
        const rate = level ? `${(level.discount_rate * 10).toFixed(1)}折` : ''
        return (
          <Space>
            <Tag color="purple">{name}</Tag>
            {rate && <Tag color="orange">{rate}</Tag>}
          </Space>
        )
      }
    },
    { title: '余额', dataIndex: 'balance', key: 'balance',
      render: (val: number) => <span style={{ color: '#52c41a', fontWeight: 600 }}>¥{val.toFixed(2)}</span>
    },
    { title: '累计充值', dataIndex: 'total_recharge', key: 'total_recharge',
      render: (val: number) => <span>¥{val.toFixed(2)}</span>
    },
    { title: '累计消费', dataIndex: 'total_consumption', key: 'total_consumption',
      render: (val: number) => <span>¥{val.toFixed(2)}</span>
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === '正常' ? 'green' : 'red'}>{status}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Member) => (
        <Space size="small">
          <Button icon={<HistoryOutlined />} size="small" onClick={() => handleViewDetail(record)}>详情</Button>
          <Button icon={<WalletOutlined />} size="small" type="primary" onClick={() => handleRecharge(record)}>充值</Button>
          <Button icon={<EditOutlined />} size="small" onClick={() => handleEditMember(record)}>编辑</Button>
          <Button icon={<DeleteOutlined />} size="small" danger onClick={() => handleDeleteMember(record.member_no)}>删除</Button>
        </Space>
      ),
    },
  ]

  const levelColumns = [
    { title: '等级编号', dataIndex: 'level_id', key: 'level_id' },
    { title: '等级名称', dataIndex: 'name', key: 'name' },
    { title: '最低充值门槛', dataIndex: 'min_recharge', key: 'min_recharge',
      render: (val: number) => <span>¥{val.toFixed(2)}</span>
    },
    { title: '折扣率', dataIndex: 'discount_rate', key: 'discount_rate',
      render: (val: number) => <Tag color="orange">{(val * 10).toFixed(1)} 折</Tag>
    },
    { title: '描述', dataIndex: 'description', key: 'description' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === '启用' ? 'green' : 'default'}>{status}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: MemberLevel) => (
        <Space size="small">
          <Button icon={<EditOutlined />} size="small" onClick={() => handleEditLevel(record)}>编辑</Button>
          <Button icon={<DeleteOutlined />} size="small" danger onClick={() => handleDeleteLevel(record.level_id)}>删除</Button>
        </Space>
      ),
    },
  ]

  const consumptionColumns = [
    { title: '消费单号', dataIndex: 'consumption_no', key: 'consumption_no' },
    { title: '会员姓名', dataIndex: 'member_name', key: 'member_name' },
    { title: '联系电话', dataIndex: 'phone', key: 'phone' },
    { title: '服务项目', dataIndex: 'service_name', key: 'service_name' },
    { title: '原价', dataIndex: 'original_price', key: 'original_price',
      render: (val: number) => <span>¥{val.toFixed(2)}</span>
    },
    { title: '折扣', dataIndex: 'discount_rate', key: 'discount_rate',
      render: (val: number) => val < 1 ? <Tag color="orange">{(val * 10).toFixed(1)}折</Tag> : '无'
    },
    { title: '实付金额', dataIndex: 'actual_amount', key: 'actual_amount',
      render: (val: number) => <span style={{ fontWeight: 600 }}>¥{val.toFixed(2)}</span>
    },
    {
      title: '支付方式',
      dataIndex: 'pay_method',
      key: 'pay_method',
      render: (method: string) => (
        <Tag color={method === '余额' ? 'blue' : 'green'}>{method}</Tag>
      ),
    },
    { title: '操作人', dataIndex: 'operator', key: 'operator' },
    { title: '消费时间', dataIndex: 'created_at', key: 'created_at',
      render: (val: string) => new Date(val).toLocaleString()
    },
  ]

  const rechargeColumns = [
    { title: '充值单号', dataIndex: 'recharge_no', key: 'recharge_no' },
    { title: '充值金额', dataIndex: 'recharge_amount', key: 'recharge_amount',
      render: (val: number) => <span style={{ color: '#52c41a', fontWeight: 600 }}>¥{val.toFixed(2)}</span>
    },
    { title: '赠送金额', dataIndex: 'gift_amount', key: 'gift_amount',
      render: (val: number) => <span style={{ color: '#faad14' }}>¥{val.toFixed(2)}</span>
    },
    { title: '到账合计', dataIndex: 'total_amount', key: 'total_amount',
      render: (val: number) => <span style={{ fontWeight: 600 }}>¥{val.toFixed(2)}</span>
    },
    { title: '充值前余额', dataIndex: 'balance_before', key: 'balance_before',
      render: (val: number) => <span>¥{val.toFixed(2)}</span>
    },
    { title: '充值后余额', dataIndex: 'balance_after', key: 'balance_after',
      render: (val: number) => <span style={{ color: '#52c41a' }}>¥{val.toFixed(2)}</span>
    },
    { title: '操作人', dataIndex: 'operator', key: 'operator' },
    { title: '充值时间', dataIndex: 'created_at', key: 'created_at',
      render: (val: string) => new Date(val).toLocaleString()
    },
  ]

  const logColumns = [
    { title: '日志编号', dataIndex: 'log_id', key: 'log_id' },
    { title: '操作人', dataIndex: 'operator', key: 'operator' },
    { title: '模块', dataIndex: 'module', key: 'module',
      render: (m: string) => <Tag color="blue">{m}</Tag>
    },
    { title: '操作类型', dataIndex: 'action', key: 'action',
      render: (a: string) => <Tag color="purple">{a}</Tag>
    },
    { title: '目标对象', dataIndex: 'target_id', key: 'target_id' },
    { title: '详情', dataIndex: 'detail', key: 'detail' },
    { title: '时间', dataIndex: 'created_at', key: 'created_at',
      render: (val: string) => new Date(val).toLocaleString()
    },
  ]

  const memberConsumptionColumns = [
    { title: '消费单号', dataIndex: 'consumption_no', key: 'consumption_no' },
    { title: '服务项目', dataIndex: 'service_name', key: 'service_name' },
    { title: '原价', dataIndex: 'original_price', key: 'original_price',
      render: (val: number) => <span>¥{val.toFixed(2)}</span>
    },
    { title: '实付', dataIndex: 'actual_amount', key: 'actual_amount',
      render: (val: number) => <span style={{ fontWeight: 600 }}>¥{val.toFixed(2)}</span>
    },
    { title: '支付方式', dataIndex: 'pay_method', key: 'pay_method',
      render: (m: string) => <Tag color={m === '余额' ? 'blue' : 'green'}>{m}</Tag>
    },
    { title: '余额后', dataIndex: 'balance_after', key: 'balance_after',
      render: (val?: number) => val !== undefined ? <span>¥{val.toFixed(2)}</span> : '-'
    },
    { title: '操作人', dataIndex: 'operator', key: 'operator' },
    { title: '时间', dataIndex: 'created_at', key: 'created_at',
      render: (val: string) => new Date(val).toLocaleString()
    },
  ]

  const total_balance = members.reduce((sum, m) => sum + m.balance, 0)
  const total_recharge = members.reduce((sum, m) => sum + m.total_recharge, 0)
  const total_consumption = members.reduce((sum, m) => sum + m.total_consumption, 0)

  const tabItems = [
    {
      key: 'members',
      label: <span><UserOutlined />会员档案</span>,
      children: (
        <Card
          extra={
            <Space>
              <Button type="primary" icon={<PlusOutlined />} onClick={handleAddMember}>新增会员</Button>
              <Button icon={<ReloadOutlined />} onClick={fetchMembers}>刷新</Button>
            </Space>
          }
        >
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Statistic title="会员总数" value={members.length} prefix={<UserOutlined />} />
            </Col>
            <Col span={6}>
              <Statistic title="储值总额" value={total_balance} precision={2} prefix="¥" valueStyle={{ color: '#52c41a' }} />
            </Col>
            <Col span={6}>
              <Statistic title="累计充值" value={total_recharge} precision={2} prefix="¥" />
            </Col>
            <Col span={6}>
              <Statistic title="累计消费" value={total_consumption} precision={2} prefix="¥" valueStyle={{ color: '#1890ff' }} />
            </Col>
          </Row>
          <Card size="small" style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col span={6}>
                <Input
                  placeholder="搜索姓名"
                  allowClear
                  value={memberFilters.name}
                  onChange={(e) => setMemberFilters({ ...memberFilters, name: e.target.value })}
                  onPressEnter={fetchMembers}
                />
              </Col>
              <Col span={6}>
                <Input
                  placeholder="搜索手机号"
                  allowClear
                  value={memberFilters.phone}
                  onChange={(e) => setMemberFilters({ ...memberFilters, phone: e.target.value })}
                  onPressEnter={fetchMembers}
                />
              </Col>
              <Col span={6}>
                <Select
                  placeholder="选择会员等级"
                  allowClear
                  style={{ width: '100%' }}
                  value={memberFilters.level_id || undefined}
                  onChange={(value) => setMemberFilters({ ...memberFilters, level_id: value || '' })}
                  options={levels.map(l => ({ value: l.level_id, label: l.name }))}
                />
              </Col>
              <Col span={6}>
                <Space>
                  <Select
                    placeholder="状态"
                    allowClear
                    style={{ width: 120 }}
                    value={memberFilters.status || undefined}
                    onChange={(value) => setMemberFilters({ ...memberFilters, status: value || '' })}
                    options={[{ value: '正常', label: '正常' }, { value: '停用', label: '停用' }]}
                  />
                  <Button onClick={fetchMembers} type="primary">查询</Button>
                  <Button onClick={() => {
                    setMemberFilters({ name: '', phone: '', level_id: '', status: '' })
                    fetchMembers()
                  }}>重置</Button>
                </Space>
              </Col>
            </Row>
          </Card>
          <Table columns={memberColumns} dataSource={members} rowKey="id" loading={loading} />
        </Card>
      ),
    },
    {
      key: 'levels',
      label: <span><CrownOutlined />会员等级</span>,
      children: (
        <Card
          extra={
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAddLevel}>新增等级</Button>
          }
        >
          <Table columns={levelColumns} dataSource={levels} rowKey="id" loading={loading} />
        </Card>
      ),
    },
    {
      key: 'consumptions',
      label: <span><HistoryOutlined />消费记录</span>,
      children: (
        <Card
          extra={
            <Space>
              <Select
                placeholder="支付方式"
                allowClear
                style={{ width: 160 }}
                value={consumptionFilters.pay_method || undefined}
                onChange={(value) => setConsumptionFilters({ pay_method: value || '' })}
                options={[{ value: '余额', label: '余额' }, { value: '现金', label: '现金' }]}
              />
              <Button type="primary" onClick={fetchConsumptions}>查询</Button>
            </Space>
          }
        >
          <Table columns={consumptionColumns} dataSource={consumptions} rowKey="id" loading={loading} />
        </Card>
      ),
    },
    {
      key: 'logs',
      label: <span><HistoryOutlined />操作日志</span>,
      children: (
        <Card
          extra={
            <Space>
              <Select
                placeholder="模块"
                allowClear
                style={{ width: 160 }}
                value={logFilters.module || undefined}
                onChange={(value) => setLogFilters({ ...logFilters, module: value || '' })}
                options={[
                  { value: '会员等级', label: '会员等级' },
                  { value: '会员档案', label: '会员档案' },
                  { value: '会员储值', label: '会员储值' },
                  { value: '预约服务', label: '预约服务' },
                ]}
              />
              <Input
                placeholder="操作人"
                allowClear
                style={{ width: 160 }}
                value={logFilters.operator}
                onChange={(e) => setLogFilters({ ...logFilters, operator: e.target.value })}
              />
              <Button type="primary" onClick={fetchLogs}>查询</Button>
            </Space>
          }
        >
          <Table columns={logColumns} dataSource={logs} rowKey="id" loading={loading} />
        </Card>
      ),
    },
  ]

  return (
    <Card title="会员储值与消费管理">
      <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />

      <Modal
        title={editingMember ? '编辑会员' : '新增会员'}
        open={memberModalVisible}
        onCancel={() => setMemberModalVisible(false)}
        footer={null}
        width={560}
      >
        <Form form={memberForm} layout="vertical" onFinish={handleMemberSubmit}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="member_no"
                label="会员编号"
                rules={[{ required: !editingMember, message: '请输入会员编号' }]}
              >
                <Input disabled={!!editingMember} placeholder="留空自动生成" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="name"
                label="姓名"
                rules={[{ required: true, message: '请输入姓名' }]}
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
              <Form.Item name="gender" label="性别">
                <Select options={[{ value: '男', label: '男' }, { value: '女', label: '女' }]} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="level_id"
                label="会员等级"
                rules={[{ required: true, message: '请选择会员等级' }]}
              >
                <Select
                  onChange={(value) => {
                    const level = levels.find(l => l.level_id === value)
                    memberForm.setFieldsValue({ level_name: level?.name || '' })
                  }}
                  options={levels.filter(l => l.status === '启用').map(l => ({ value: l.level_id, label: `${l.name} (${(l.discount_rate * 10).toFixed(1)}折)` }))}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="level_name" hidden>
                <Input />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="balance" label="初始余额">
                <InputNumber style={{ width: '100%' }} min={0} precision={2} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="status" label="状态">
                <Select options={[{ value: '正常', label: '正常' }, { value: '停用', label: '停用' }]} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>提交</Button>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={editingLevel ? '编辑会员等级' : '新增会员等级'}
        open={levelModalVisible}
        onCancel={() => setLevelModalVisible(false)}
        footer={null}
        width={500}
      >
        <Form form={levelForm} layout="vertical" onFinish={handleLevelSubmit}>
          <Form.Item
            name="level_id"
            label="等级编号"
            rules={[{ required: !editingLevel, message: '请输入等级编号' }]}
          >
            <Input disabled={!!editingLevel} placeholder="留空自动生成" />
          </Form.Item>
          <Form.Item
            name="name"
            label="等级名称"
            rules={[{ required: true, message: '请输入等级名称' }]}
          >
            <Input placeholder="如：普通会员、银卡会员、金卡会员" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="min_recharge"
                label="最低充值门槛(元)"
                rules={[{ required: true, message: '请输入最低充值门槛' }]}
              >
                <InputNumber style={{ width: '100%' }} min={0} precision={2} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="discount_rate"
                label="折扣率(0-1，如0.9为9折)"
                rules={[{ required: true, message: '请输入折扣率' }]}
              >
                <InputNumber style={{ width: '100%' }} min={0} max={1} step={0.05} precision={2} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="description" label="等级描述">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="status" label="状态">
            <Select options={[{ value: '启用', label: '启用' }, { value: '禁用', label: '禁用' }]} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>提交</Button>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`为会员充值 - ${rechargingMember?.name || ''}`}
        open={rechargeModalVisible}
        onCancel={() => setRechargeModalVisible(false)}
        footer={null}
        width={460}
      >
        {rechargingMember && (
          <>
            <Descriptions size="small" column={1} style={{ marginBottom: 16 }} bordered>
              <Descriptions.Item label="会员编号">{rechargingMember.member_no}</Descriptions.Item>
              <Descriptions.Item label="姓名">{rechargingMember.name}</Descriptions.Item>
              <Descriptions.Item label="当前余额">¥{rechargingMember.balance.toFixed(2)}</Descriptions.Item>
              <Descriptions.Item label="会员等级">{rechargingMember.level_name}</Descriptions.Item>
            </Descriptions>
            <Form form={rechargeForm} layout="vertical" onFinish={handleRechargeSubmit}>
              <Form.Item
                name="recharge_amount"
                label="充值金额(元)"
                rules={[{ required: true, message: '请输入充值金额' }]}
              >
                <InputNumber style={{ width: '100%' }} min={0.01} precision={2} />
              </Form.Item>
              <Form.Item name="gift_amount" label="赠送金额(元)">
                <InputNumber style={{ width: '100%' }} min={0} precision={2} />
              </Form.Item>
              <Form.Item name="remark" label="备注">
                <Input.TextArea rows={2} />
              </Form.Item>
              <Form.Item>
                <Button type="primary" htmlType="submit" block>确认充值</Button>
              </Form.Item>
            </Form>
          </>
        )}
      </Modal>

      <Modal
        title={`会员详情 - ${detailMember?.name || ''}`}
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={900}
      >
        {detailMember && (
          <>
            <Descriptions size="small" column={3} style={{ marginBottom: 16 }} bordered>
              <Descriptions.Item label="会员编号">{detailMember.member_no}</Descriptions.Item>
              <Descriptions.Item label="姓名">{detailMember.name}</Descriptions.Item>
              <Descriptions.Item label="联系电话">{detailMember.phone}</Descriptions.Item>
              <Descriptions.Item label="会员等级">{detailMember.level_name}</Descriptions.Item>
              <Descriptions.Item label="当前余额" contentStyle={{ color: '#52c41a', fontWeight: 600 }}>¥{detailMember.balance.toFixed(2)}</Descriptions.Item>
              <Descriptions.Item label="状态">{detailMember.status}</Descriptions.Item>
              <Descriptions.Item label="累计充值">¥{detailMember.total_recharge.toFixed(2)}</Descriptions.Item>
              <Descriptions.Item label="累计消费">¥{detailMember.total_consumption.toFixed(2)}</Descriptions.Item>
              <Descriptions.Item label="注册时间">{new Date(detailMember.created_at).toLocaleString()}</Descriptions.Item>
            </Descriptions>
            <Divider orientation="left">充值记录</Divider>
            <Table
              columns={rechargeColumns}
              dataSource={recharges}
              rowKey="id"
              loading={detailLoading}
              size="small"
              pagination={{ pageSize: 5 }}
            />
            <Divider orientation="left">消费记录</Divider>
            <Table
              columns={memberConsumptionColumns}
              dataSource={consumptions}
              rowKey="id"
              loading={detailLoading}
              size="small"
              pagination={{ pageSize: 5 }}
            />
          </>
        )}
      </Modal>
    </Card>
  )
}

export default MemberPage
