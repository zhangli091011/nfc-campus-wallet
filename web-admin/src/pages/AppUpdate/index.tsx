import { useState, useEffect } from 'react'
import {
  Card,
  Button,
  Upload,
  Form,
  Input,
  InputNumber,
  Switch,
  message,
  Typography,
  Descriptions,
  Tag,
  Space,
} from 'antd'
import { UploadOutlined, CloudUploadOutlined, AndroidOutlined } from '@ant-design/icons'
import request from '@/utils/request'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { TextArea } = Input

interface VersionInfo {
  has_version: boolean
  version_name?: string
  version_code?: number
  release_notes?: string
  file_size?: number
  uploaded_at?: string
  uploaded_by?: string
  force_update?: boolean
  filename?: string
}

const AppUpdate = () => {
  const [currentVersion, setCurrentVersion] = useState<VersionInfo | null>(null)
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    loadCurrentVersion()
  }, [])

  const loadCurrentVersion = async () => {
    setLoading(true)
    try {
      const res = await request.get<any, VersionInfo>('/app-update/info')
      setCurrentVersion(res)
    } catch {
      setCurrentVersion(null)
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async () => {
    try {
      const values = await form.validateFields()
      const fileList = values.file
      if (!fileList || fileList.length === 0) {
        message.error('请选择 APK 文件')
        return
      }

      setUploading(true)

      const formData = new FormData()
      formData.append('file', fileList[0].originFileObj)
      formData.append('version_name', values.version_name)
      formData.append('version_code', values.version_code.toString())
      formData.append('release_notes', values.release_notes || '')
      formData.append('force_update', values.force_update ? 'true' : 'false')

      const token = localStorage.getItem('nfc_wallet_token')
      const response = await fetch('/api/app-update/upload', {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      })

      const result = await response.json()
      if (response.ok && result.success) {
        message.success(result.message || '上传成功')
        form.resetFields()
        loadCurrentVersion()
      } else {
        message.error(result.detail || result.message || '上传失败')
      }
    } catch (error: any) {
      message.error('上传失败: ' + (error.message || '未知错误'))
    } finally {
      setUploading(false)
    }
  }

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '-'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  }

  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>
        <AndroidOutlined /> 应用版本管理 (OTA)
      </Title>

      {/* 当前版本信息 */}
      <Card title="当前发布版本" style={{ marginBottom: 24 }} loading={loading}>
        {currentVersion?.has_version ? (
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="版本名称">
              <Tag color="blue">v{currentVersion.version_name}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="版本号">
              {currentVersion.version_code}
            </Descriptions.Item>
            <Descriptions.Item label="文件大小">
              {formatFileSize(currentVersion.file_size)}
            </Descriptions.Item>
            <Descriptions.Item label="强制更新">
              {currentVersion.force_update ? (
                <Tag color="red">是</Tag>
              ) : (
                <Tag color="green">否</Tag>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="上传时间" span={2}>
              {currentVersion.uploaded_at
                ? dayjs(currentVersion.uploaded_at).format('YYYY-MM-DD HH:mm:ss')
                : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="上传者">
              {currentVersion.uploaded_by || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="文件名">
              {currentVersion.filename || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="更新说明" span={2}>
              <Text>{currentVersion.release_notes || '无'}</Text>
            </Descriptions.Item>
          </Descriptions>
        ) : (
          <Text type="secondary">暂无已发布版本</Text>
        )}
      </Card>

      {/* 上传新版本 */}
      <Card title="上传新版本">
        <Form form={form} layout="vertical" style={{ maxWidth: 600 }}>
          <Form.Item
            name="file"
            label="APK 文件"
            valuePropName="fileList"
            getValueFromEvent={(e) => (Array.isArray(e) ? e : e?.fileList)}
            rules={[{ required: true, message: '请选择 APK 文件' }]}
          >
            <Upload
              accept=".apk"
              maxCount={1}
              beforeUpload={() => false}
              listType="text"
            >
              <Button icon={<UploadOutlined />}>选择 APK 文件</Button>
            </Upload>
          </Form.Item>

          <Space style={{ width: '100%' }} size="large">
            <Form.Item
              name="version_name"
              label="版本名称"
              rules={[{ required: true, message: '请输入版本名称' }]}
              style={{ width: 200 }}
            >
              <Input placeholder="如 1.1.0" />
            </Form.Item>

            <Form.Item
              name="version_code"
              label="版本号"
              rules={[{ required: true, message: '请输入版本号' }]}
              style={{ width: 150 }}
            >
              <InputNumber min={1} placeholder="如 2" style={{ width: '100%' }} />
            </Form.Item>
          </Space>

          <Form.Item name="release_notes" label="更新说明">
            <TextArea rows={4} placeholder="本次更新内容..." />
          </Form.Item>

          <Form.Item name="force_update" label="强制更新" valuePropName="checked">
            <Switch checkedChildren="强制" unCheckedChildren="可选" />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              icon={<CloudUploadOutlined />}
              onClick={handleUpload}
              loading={uploading}
              size="large"
            >
              发布新版本
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default AppUpdate
