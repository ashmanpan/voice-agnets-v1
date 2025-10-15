export interface Call {
  id: number;
  contact_id: number;
  contact_name?: string;
  contact_phone?: string;
  call_type: string;
  direction: 'inbound' | 'outbound';
  status: 'queued' | 'initiated' | 'in-progress' | 'completed' | 'failed' | 'no-answer' | 'busy';
  duration_seconds?: number;
  created_at: string;
  started_at?: string;
  ended_at?: string;
  caller_name?: string;
  custom_greeting?: string;
  room_name?: string;
  livekit_room_sid?: string;
}

export interface Contact {
  id: number;
  name: string;
  phone_number: string;
  contact_type: 'friend' | 'facility' | 'general';
  email?: string;
  notes?: string;
  created_at: string;
  last_called_at?: string;
  total_calls?: number;
}

export interface Task {
  id: number;
  contact_id: number;
  contact_name?: string;
  contact_phone?: string;
  assigned_call_id?: number;
  title: string;
  description: string;
  task_type: string;
  agent_script?: string;
  questions_to_ask?: string[];
  collect_response: boolean;
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high';
  contact_response?: string;
  response_sentiment?: string;
  task_completed: boolean;
  scheduled_time?: string;
  call_attempts: number;
  max_attempts: number;
  created_at: string;
  created_by: string;
  completed_at?: string;
  last_attempt_at?: string;
  notes?: string;
}

export interface ActionItem {
  id: number;
  call_id?: number;
  contact_id?: number;
  contact_name?: string;
  action_type: 'question' | 'request' | 'complaint' | 'follow_up';
  description: string;
  priority: 'low' | 'medium' | 'high';
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  assigned_to?: string;
  created_at: string;
  due_date?: string;
  completed_at?: string;
  notes?: string;
  urgency_score: number;
  source_text?: string;
}

export interface TranscriptSegment {
  id: number;
  call_id: number;
  speaker: 'agent' | 'user';
  text: string;
  sequence_number: number;
  timestamp: string;
}

export interface CallAnalysis {
  id: number;
  call_id: number;
  summary: string;
  action_items?: string;
  requests?: string;
  complaints?: string;
  sentiment: string;
  call_outcome: string;
  analyzed_at: string;
}

export interface DashboardStats {
  total_calls: number;
  today_calls: number;
  success_rate: number;
  pending_tasks: number;
  pending_actions: number;
}
