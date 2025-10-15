import { apiClient } from './client';
import type { Task } from '../types';

export const tasksApi = {
  // Get all tasks
  getTasks: async (params?: {
    status?: string;
    priority?: string;
    limit?: number;
  }) => {
    const response = await apiClient.get<{ success: boolean; tasks: Task[]; count: number }>('/api/tasks', { params });
    return response.data;
  },

  // Get task by ID
  getTaskById: async (id: number) => {
    const response = await apiClient.get<Task>(`/api/tasks/${id}`);
    return response.data;
  },

  // Update task
  updateTask: async (id: number, data: Partial<Task>) => {
    const response = await apiClient.patch(`/api/tasks/${id}`, data);
    return response.data;
  },

  // Assign new task
  assignTask: async (data: {
    contact_id: number;
    title: string;
    description: string;
    task_type: string;
    agent_script?: string;
    questions_to_ask?: string[];
    priority?: string;
    scheduled_time?: string;
    created_by?: string;
  }) => {
    const response = await apiClient.post('/api/tasks/assign', data);
    return response.data;
  },

  // Initiate task delivery call
  initiateTaskCall: async (taskId: number) => {
    const response = await apiClient.post(`/api/tasks/${taskId}/call`);
    return response.data;
  },
};
