/**
 * Report Service
 * 
 * 报表服务：提供报表、排行榜、审计日志和导出功能
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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
// API Functions
// ============================================================================

/**
 * 获取总览统计报表
 */
export const getSummaryReport = async (eventId?: number): Promise<SummaryReport> => {
  const token = localStorage.getItem('token');
  const params = eventId ? { event_id: eventId } : {};
  
  const response = await axios.get(`${API_BASE_URL}/reports/summary`, {
    params,
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  
  return response.data;
};

/**
 * 获取摊位维度报表
 */
export const getBoothReport = async (eventId?: number): Promise<BoothReportResponse> => {
  const token = localStorage.getItem('token');
  const params = eventId ? { event_id: eventId } : {};
  
  const response = await axios.get(`${API_BASE_URL}/reports/booths`, {
    params,
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  
  return response.data;
};

/**
 * 获取商品维度报表
 */
export const getProductReport = async (
  eventId?: number,
  boothId?: number
): Promise<ProductReportResponse> => {
  const token = localStorage.getItem('token');
  const params: any = {};
  if (eventId) params.event_id = eventId;
  if (boothId) params.booth_id = boothId;
  
  const response = await axios.get(`${API_BASE_URL}/reports/products`, {
    params,
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  
  return response.data;
};

/**
 * 获取营业额排行榜
 */
export const getRevenueLeaderboard = async (
  eventId?: number,
  limit: number = 10
): Promise<LeaderboardResponse> => {
  const token = localStorage.getItem('token');
  const params: any = { limit };
  if (eventId) params.event_id = eventId;
  
  const response = await axios.get(`${API_BASE_URL}/leaderboard/revenue`, {
    params,
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  
  return response.data;
};

/**
 * 获取利润排行榜
 */
export const getProfitLeaderboard = async (
  eventId?: number,
  limit: number = 10
): Promise<LeaderboardResponse> => {
  const token = localStorage.getItem('token');
  const params: any = { limit };
  if (eventId) params.event_id = eventId;
  
  const response = await axios.get(`${API_BASE_URL}/leaderboard/profit`, {
    params,
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  
  return response.data;
};

/**
 * 获取利润率排行榜
 */
export const getRoiLeaderboard = async (
  eventId?: number,
  limit: number = 10
): Promise<LeaderboardResponse> => {
  const token = localStorage.getItem('token');
  const params: any = { limit };
  if (eventId) params.event_id = eventId;
  
  const response = await axios.get(`${API_BASE_URL}/leaderboard/roi`, {
    params,
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  
  return response.data;
};

/**
 * 获取商品排行榜
 */
export const getProductLeaderboard = async (
  metric: 'sales' | 'revenue' | 'profit' = 'sales',
  eventId?: number,
  limit: number = 10
): Promise<ProductLeaderboardResponse> => {
  const token = localStorage.getItem('token');
  const params: any = { metric, limit };
  if (eventId) params.event_id = eventId;
  
  const response = await axios.get(`${API_BASE_URL}/leaderboard/products`, {
    params,
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  
  return response.data;
};

/**
 * 获取异常审计日志
 */
export const getAuditLogs = async (
  eventId?: number,
  flagType: string = 'all',
  limit: number = 100
): Promise<AuditLogResponse> => {
  const token = localStorage.getItem('token');
  const params: any = { flag_type: flagType, limit };
  if (eventId) params.event_id = eventId;
  
  const response = await axios.get(`${API_BASE_URL}/reports/audit-logs`, {
    params,
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  
  return response.data;
};

/**
 * 导出报表为 Excel
 */
export const exportReportExcel = async (
  reportType: 'summary' | 'booths' | 'products' | 'transactions',
  eventId?: number
): Promise<Blob> => {
  const token = localStorage.getItem('token');
  const params: any = { report_type: reportType };
  if (eventId) params.event_id = eventId;
  
  const response = await axios.get(`${API_BASE_URL}/reports/export/excel`, {
    params,
    headers: {
      Authorization: `Bearer ${token}`,
    },
    responseType: 'blob',
  });
  
  return response.data;
};

/**
 * 下载 Excel 文件
 */
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
