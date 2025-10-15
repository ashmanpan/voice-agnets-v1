import { apiClient } from './client';
import type { ActionItem } from '../types';

export const actionsApi = {
  // Get all actions
  getActions: async (params?: {
    status?: string;
    priority?: string;
    action_type?: string;
    limit?: number;
  }) => {
    const response = await apiClient.get<{ success: boolean; actions: ActionItem[]; count: number }>('/api/actions', { params });
    return response.data;
  },

  // Get action by ID
  getActionById: async (id: number) => {
    const response = await apiClient.get<ActionItem>(`/api/actions/${id}`);
    return response.data;
  },

  // Update action
  updateAction: async (id: number, data: Partial<ActionItem>) => {
    const response = await apiClient.patch(`/api/actions/${id}`, data);
    return response.data;
  },
};
