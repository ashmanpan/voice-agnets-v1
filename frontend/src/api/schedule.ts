import { apiClient } from './client';

export interface ScheduledCall {
  id: number;
  contact_id: number;
  contact_name?: string;
  contact_phone?: string;
  call_type: string;
  scheduled_time?: string;
  is_recurring: boolean;
  is_scheduled: boolean;
  recurrence_pattern?: 'daily' | 'weekly' | 'monthly';
  recurrence_time?: string;
  recurrence_day?: string;
  is_active: boolean;
  status: string;
  caller_name?: string;
  custom_greeting?: string;
  custom_subject?: string;
  custom_message?: string;
}

export interface ScheduleCallRequest {
  name: string;
  phone: string;
  call_type: string;
  scheduled_time: string;
  caller_name?: string;
  custom_greeting?: string;
  custom_subject?: string;
  custom_message?: string;
}

export interface RecurringCallRequest {
  name: string;
  phone: string;
  call_type: string;
  recurrence_pattern: 'daily' | 'weekly' | 'monthly';
  recurrence_time: string;
  recurrence_day?: string;
  caller_name?: string;
  custom_greeting?: string;
  custom_subject?: string;
  custom_message?: string;
}

export const scheduleApi = {
  // Get all scheduled calls
  getScheduledCalls: async () => {
    const response = await apiClient.get<{ calls: ScheduledCall[] }>('/api/calls', {
      params: { is_scheduled: true }
    });
    return response.data.calls || [];
  },

  // Get all recurring calls
  getRecurringCalls: async () => {
    const response = await apiClient.get<{ calls: ScheduledCall[] }>('/api/calls', {
      params: { is_recurring: true }
    });
    return response.data.calls || [];
  },

  // Schedule a one-time call
  scheduleCall: async (data: ScheduleCallRequest) => {
    const formData = new FormData();
    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        formData.append(key, value);
      }
    });
    const response = await apiClient.post('/api/calls/schedule', formData);
    return response.data;
  },

  // Create recurring call
  createRecurringCall: async (data: RecurringCallRequest) => {
    const formData = new FormData();
    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        formData.append(key, value);
      }
    });
    const response = await apiClient.post('/api/calls/recurring', formData);
    return response.data;
  },

  // Pause recurring call
  pauseRecurringCall: async (callId: number) => {
    const response = await apiClient.post(`/api/calls/${callId}/pause`);
    return response.data;
  },

  // Resume recurring call
  resumeRecurringCall: async (callId: number) => {
    const response = await apiClient.post(`/api/calls/${callId}/resume`);
    return response.data;
  },

  // Cancel call
  cancelCall: async (callId: number) => {
    const response = await apiClient.post(`/api/calls/${callId}/cancel`);
    return response.data;
  },
};
