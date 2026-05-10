# 🔗 数据大屏集成指南

## 快速集成步骤

### 1. 安装依赖

```bash
cd web-admin
npm install echarts
```

### 2. 导入路由

在 `src/App.tsx` 中添加路由：

```typescript
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import StockDashboard from './pages/StockDashboard';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 其他路由 */}
        <Route path="/dashboard" element={<StockDashboard />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

### 3. 配置环境变量

创建或编辑 `.env` 文件：

```env
VITE_API_URL=http://localhost:8000
```

### 4. 启动应用

```bash
npm run dev
```

### 5. 访问大屏

打开浏览器访问：`http://localhost:5173/dashboard`

---

## 完整集成示例

### App.tsx 完整代码

```typescript
import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, Spin } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import StockDashboard from './pages/StockDashboard';
import './App.css';

// 其他页面组件
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Layout from './components/Layout';

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Suspense fallback={<Spin size="large" />}>
          <Routes>
            {/* 登录页 */}
            <Route path="/login" element={<Login />} />
            
            {/* 数据大屏（全屏，无Layout） */}
            <Route path="/stock-dashboard" element={<StockDashboard />} />
            
            {/* 管理后台（带Layout） */}
            <Route path="/" element={<Layout />}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              {/* 其他管理页面 */}
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </ConfigProvider>
  );
}

export default App;
```

---

## 在主界面添加入口

### 方式1: 添加菜单项

在 `Layout.tsx` 的菜单配置中添加：

```typescript
const menuItems = [
  {
    key: 'dashboard',
    icon: <DashboardOutlined />,
    label: '数据概览',
  },
  {
    key: 'stock-dashboard',
    icon: <StockOutlined />,
    label: '股市大屏',
    onClick: () => {
      // 新窗口打开大屏
      window.open('/stock-dashboard', '_blank');
    },
  },
  // 其他菜单项...
];
```

### 方式2: 添加快捷按钮

在主页面添加快捷入口：

```typescript
import { Button } from 'antd';
import { StockOutlined } from '@ant-design/icons';

function Dashboard() {
  const openStockDashboard = () => {
    window.open('/stock-dashboard', '_blank', 'fullscreen=yes');
  };

  return (
    <div>
      <Button
        type="primary"
        size="large"
        icon={<StockOutlined />}
        onClick={openStockDashboard}
        style={{
          background: 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)',
          border: 'none',
          height: '60px',
          fontSize: '18px',
          fontWeight: 'bold',
        }}
      >
        打开股市大屏
      </Button>
    </div>
  );
}
```

---

## 权限控制

### 添加权限验证

```typescript
import { Navigate } from 'react-router-dom';

function ProtectedStockDashboard() {
  const token = localStorage.getItem('token');
  const userRole = localStorage.getItem('role');

  // 检查是否登录
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // 检查权限（可选）
  if (userRole !== 'admin' && userRole !== 'event_admin') {
    return <Navigate to="/dashboard" replace />;
  }

  return <StockDashboard />;
}

// 在路由中使用
<Route path="/stock-dashboard" element={<ProtectedStockDashboard />} />
```

---

## WebSocket实时更新（可选）

### 1. 安装WebSocket库

```bash
npm install socket.io-client
```

### 2. 创建WebSocket服务

```typescript
// src/services/websocket.ts
import { io, Socket } from 'socket.io-client';

class WebSocketService {
  private socket: Socket | null = null;

  connect(url: string) {
    this.socket = io(url, {
      transports: ['websocket'],
      autoConnect: true,
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    return this.socket;
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  on(event: string, callback: (data: any) => void) {
    if (this.socket) {
      this.socket.on(event, callback);
    }
  }

  emit(event: string, data: any) {
    if (this.socket) {
      this.socket.emit(event, data);
    }
  }
}

export default new WebSocketService();
```

### 3. 在大屏中使用WebSocket

```typescript
import { useEffect } from 'react';
import websocketService from '../services/websocket';

function StockDashboard() {
  useEffect(() => {
    // 连接WebSocket
    const socket = websocketService.connect('ws://localhost:8000');

    // 监听市场数据更新
    websocketService.on('market_update', (data) => {
      console.log('Market update:', data);
      setMarketStats(data);
    });

    // 监听摊位数据更新
    websocketService.on('booth_update', (data) => {
      console.log('Booth update:', data);
      setBoothData(data);
    });

    return () => {
      websocketService.disconnect();
    };
  }, []);

  // 其他代码...
}
```

---

## 全屏模式

### 添加全屏按钮

```typescript
import { FullscreenOutlined, FullscreenExitOutlined } from '@ant-design/icons';
import { Button } from 'antd';
import { useState } from 'react';

function StockDashboard() {
  const [isFullscreen, setIsFullscreen] = useState(false);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  return (
    <div className="stock-dashboard">
      <Button
        type="text"
        icon={isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
        onClick={toggleFullscreen}
        style={{
          position: 'fixed',
          top: 20,
          right: 20,
          zIndex: 1000,
          color: '#FFD700',
          fontSize: 24,
        }}
      />
      {/* 其他内容 */}
    </div>
  );
}
```

---

## 数据导出功能

### 添加导出按钮

```typescript
import { DownloadOutlined } from '@ant-design/icons';
import { Button, message } from 'antd';

function StockDashboard() {
  const exportData = () => {
    try {
      // 准备导出数据
      const exportData = {
        marketStats,
        boothData,
        exportTime: new Date().toISOString(),
      };

      // 转换为JSON
      const dataStr = JSON.stringify(exportData, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });

      // 创建下载链接
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `stock-market-${Date.now()}.json`;
      link.click();

      // 清理
      URL.revokeObjectURL(url);
      message.success('数据导出成功');
    } catch (error) {
      message.error('数据导出失败');
    }
  };

  return (
    <div className="stock-dashboard">
      <Button
        type="primary"
        icon={<DownloadOutlined />}
        onClick={exportData}
        style={{
          position: 'fixed',
          bottom: 20,
          right: 20,
          zIndex: 1000,
        }}
      >
        导出数据
      </Button>
      {/* 其他内容 */}
    </div>
  );
}
```

---

## 打印功能

### 添加打印样式

```css
/* StockDashboard.css */
@media print {
  .stock-dashboard {
    background: white !important;
  }

  .dashboard-header {
    background: white !important;
    border-bottom: 2px solid #000 !important;
  }

  .data-card {
    background: white !important;
    border: 1px solid #000 !important;
    page-break-inside: avoid;
  }

  /* 隐藏不需要打印的元素 */
  .no-print {
    display: none !important;
  }
}
```

### 添加打印按钮

```typescript
import { PrinterOutlined } from '@ant-design/icons';
import { Button } from 'antd';

function StockDashboard() {
  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="stock-dashboard">
      <Button
        type="primary"
        icon={<PrinterOutlined />}
        onClick={handlePrint}
        className="no-print"
      >
        打印报表
      </Button>
      {/* 其他内容 */}
    </div>
  );
}
```

---

## 性能监控

### 添加性能监控

```typescript
import { useEffect } from 'react';

function StockDashboard() {
  useEffect(() => {
    // 监控组件渲染性能
    const startTime = performance.now();

    return () => {
      const endTime = performance.now();
      console.log(`Dashboard render time: ${endTime - startTime}ms`);
    };
  }, []);

  // 监控API请求性能
  const loadData = async () => {
    const startTime = performance.now();
    
    try {
      await axios.get('/api/stock/stats/1');
      const endTime = performance.now();
      console.log(`API request time: ${endTime - startTime}ms`);
    } catch (error) {
      console.error('API request failed:', error);
    }
  };

  // 其他代码...
}
```

---

## 故障恢复

### 添加错误边界

```typescript
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Result, Button } from 'antd';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Dashboard error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Result
          status="error"
          title="数据大屏加载失败"
          subTitle={this.state.error?.message}
          extra={
            <Button type="primary" onClick={() => window.location.reload()}>
              刷新页面
            </Button>
          }
        />
      );
    }

    return this.props.children;
  }
}

// 使用
<ErrorBoundary>
  <StockDashboard />
</ErrorBoundary>
```

---

## 📞 技术支持

如有问题，请查看：
- [大屏使用文档](./STOCK_DASHBOARD_README.md)
- [API文档](../docs/API_DOCUMENTATION.md)
- [系统架构文档](../docs/STOCK_MARKET_SYSTEM.md)

---

**Made with ❤️ for campus financial education**
