/**
 * Report Service
 * 
 * 报表服务：提供报表、排行榜、审计日志和导出功能
 * 使用统一的 request 工具（自动带 token、走 Vite 代理）
 */

import request from '@/utils/request';
import axios from 'axios';
import { getToken } from '@/utils/auth';

// ============================================================================
// Types
// ============================================================================

export interface SummaryReport {
  total_issued: number;
  total_recharged: number;
  total_consumed: number;
  total_refunded: number;
  net_consumed: number;
  total_transactions: number;
  participant_count: number;
  booth_count: number;
}

export interface BoothReportItem {
  booth_id: number;
  booth_name: string;
  class_name: string;
  revenue: number;
  refund_amount: number;
  net_revenue: number;
  sales_count: number;
  total_cost: number;
  profit: number;
  profit_margin: number | null;
}

export interface BoothReportResponse {
  booths: BoothReportItem[];
  total_count: number;
}

export interface ProductReportItem {
  product_id: number;
  product_name: string;
  booth_id: number;
  booth_name: string;
  sales_quantity: number;
  revenue: number;
  total_cost: number;
  profit: number;
  profit_margin: number | null;
}

export interface ProductReportResponse {
  products: ProductReportItem[];
  total_count: number;
}

export interface LeaderboardItem {
  rank: number;
  booth_id: number;
  booth_name: string;
  class_name: string;
  value: number;
}

export interface LeaderboardResponse {
  leaderboard: LeaderboardItem[];
  metric: string;
  total_count: number;
}

export interface ProductLeaderboardItem {
  rank: number;
  product_id: number;
  product_name: string;
  booth_id: number;
  booth_name: string;
  value: number;
}

export interface ProductLeaderboardResponse {
  leaderboard: ProductLeaderboardItem[];
  metric: string;
  total_count: number;
}

export interface AuditLogItem {
  transaction_id: number;
  transaction_type: string;
  amount: number;
  participant_name: string | null;
  booth_name: string | null;
  operator_username: string | null;
  remark: string | null;
  created_at: string;
  flag_reason: string;
}

export interface AuditLogResponse {
  logs: AuditLogItem[];
  total_count: number;
}

// ============================================================================
// API Functions (使用统一 request 工具)
// ============================================================================

/** 获取总览统计报表 */
export const getSummaryReport = (eventId?: number): Promise<SummaryReport> => {
  return request.get('/reports/summary', {
    params: eventId ? { event_id: eventId } : undefined,
  });
};

/** 获取摊位维度报表 */
export const getBoothReport = (eventId?: number): Promise<BoothReportResponse> => {
  return request.get('/reports/booths', {
    params: eventId ? { event_id: eventId } : undefined,
  });
};

/** 获取商品维度报表 */
export const getProductReport = (
  eventId?: number,
  boothId?: number
): Promise<ProductReportResponse> => {
  const params: any = {};
  if (eventId) params.event_id = eventId;
  if (boothId) params.booth_id = boothId;
  return request.get('/reports/products', { params });
};

/** 获取营业额排行榜 */
export const getRevenueLeaderboard = (
  eventId?: number,
  limit: number = 10
): Promise<LeaderboardResponse> => {
  const params: any = { limit };
  if (eventId) params.event_id = eventId;
  return request.get('/leaderboard/revenue', { params });
};

/** 获取利润排行榜 */
export const getProfitLeaderboard = (
  eventId?: number,
  limit: number = 10
): Promise<LeaderboardResponse> => {
  const params: any = { limit };
  if (eventId) params.event_id = eventId;
  return request.get('/leaderboard/profit', { params });
};

/** 获取利润率排行榜 */
export const getRoiLeaderboard = (
  eventId?: number,
  limit: number = 10
): Promise<LeaderboardResponse> => {
  const params: any = { limit };
  if (eventId) params.event_id = eventId;
  return request.get('/leaderboard/roi', { params });
};

/** 获取商品排行榜 */
export const getProductLeaderboard = (
  metric: 'sales' | 'revenue' | 'profit' = 'sales',
  eventId?: number,
  limit: number = 10
): Promise<ProductLeaderboardResponse> => {
  const params: any = { metric, limit };
  if (eventId) params.event_id = eventId;
  return request.get('/leaderboard/products', { params });
};

/** 获取异常审计日志 */
export const getAuditLogs = (
  eventId?: number,
  flagType: string = 'all',
  limit: number = 100
): Promise<AuditLogResponse> => {
  const params: any = { flag_type: flagType, limit };
  if (eventId) params.event_id = eventId;
  return request.get('/reports/audit-logs', { params });
};

/** 导出报表为 Excel */
export const exportReportExcel = async (
  reportType: 'summary' | 'booths' | 'products' | 'transactions',
  eventId?: number
): Promise<Blob> => {
  const token = getToken();
  const params: any = { report_type: reportType };
  if (eventId) params.event_id = eventId;

  // 导出需要 blob 响应类型，使用 axios 直接调用（走代理）
  const response = await axios.get('/api/reports/export/excel', {
    params,
    headers: {
      Authorization: `Bearer ${token}`,
    },
    responseType: 'blob',
  });

  return response.data;
};

/** 下载 Excel 文件 */
export const downloadExcel = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

/** 按商铺导出账目明细 */
export const exportBoothTransactions = async (params: {
  booth_id: number;
  start_date?: string;
  end_date?: string;
  has_product?: boolean;
}): Promise<Blob> => {
  const token = getToken();

  const response = await axios.get('/api/export/booth-transactions', {
    params,
    headers: {
      Authorization: `Bearer ${token}`,
    },
    responseType: 'blob',
  });

  return response.data;
};
