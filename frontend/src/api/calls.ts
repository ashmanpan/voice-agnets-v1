import { apiClient } from './client';
import type { Call, TranscriptSegment, CallAnalysis } from '../types';

export const callsApi = {
  // Get all calls
  getCalls: async (params?: {
    limit?: number;
    call_type?: string;
    status?: string;
  }) => {
    const response = await apiClient.get<{ success: boolean; calls: Call[]; count: number }>('/api/calls', { params });
    return response.data;
  },

  // Get call by ID with transcript
  getCallById: async (id: number) => {
    const response = await apiClient.get<Call>(`/api/calls/${id}`);
    return response.data;
  },

  // Get call transcript
  getCallTranscript: async (id: number) => {
    const response = await apiClient.get<{ success: boolean; transcript: TranscriptSegment[] }>(`/api/calls/${id}/transcript`);
    return response.data;
  },

  // Get call analysis
  getCallAnalysis: async (id: number) => {
    const response = await apiClient.get<{ success: boolean; analysis: CallAnalysis }>(`/api/calls/${id}/analysis`);
    return response.data;
  },

  // Initiate a call
  initiateCall: async (data: {
    name: string;
    phone: string;
    custom_greeting?: string;
    caller_name?: string;
  }) => {
    const formData = new FormData();
    formData.append('name', data.name);
    formData.append('phone', data.phone);
    if (data.custom_greeting) formData.append('custom_greeting', data.custom_greeting);
    if (data.caller_name) formData.append('caller_name', data.caller_name);

    const response = await apiClient.post('/api/calls/livekit-call', formData);
    return response.data;
  },
};
