/**
 * Dashboard Routes Configuration
 * 
 * 数据大屏路由配置
 */

import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';

// 懒加载大屏组件
const StockDashboard = lazy(() => import('../pages/StockDashboard'));

export const dashboardRoutes: RouteObject[] = [
  {
    path: '/dashboard',
    element: <StockDashboard />,
  },
  {
    path: '/stock-dashboard',
    element: <StockDashboard />,
  },
];

export default dashboardRoutes;
