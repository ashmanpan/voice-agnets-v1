import { apiClient } from './client';

export interface DailyReport {
  success: boolean;
  report_date: string;
  total_calls: number;
  completed_calls: number;
  failed_calls: number;
  success_rate: number;
  total_duration_minutes: number;
  average_duration_seconds: number;
  call_types: Record<string, number>;
  sentiments: Record<string, number>;
  top_contacts: Array<{
    name: string;
    phone: string;
    call_count: number;
  }>;
}

export interface SummaryReport {
  success: boolean;
  period_days: number;
  total_calls: number;
  completed_calls: number;
  success_rate: number;
  total_duration_minutes: number;
  average_calls_per_day: number;
  call_volume_by_day: Array<{
    date: string;
    count: number;
  }>;
  call_types: Record<string, number>;
  sentiments: Record<string, number>;
}

export const reportsApi = {
  // Get daily report
  getDailyReport: async (date?: string) => {
    const params = date ? { date } : {};
    const response = await apiClient.post<DailyReport>('/api/reports/daily', null, { params });
    return response.data;
  },

  // Get summary report for last N days
  getSummaryReport: async (days: number = 7) => {
    const response = await apiClient.get<SummaryReport>('/api/reports/summary', {
      params: { days }
    });
    return response.data;
  },

  // Get daily report as text
  getDailyReportText: async (date?: string) => {
    const params = date ? { date, format: 'text' } : { format: 'text' };
    const response = await apiClient.post('/api/reports/daily', null, { params });
    return response.data;
  },
};
