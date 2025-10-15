import { Clock, Phone, CheckCircle } from 'lucide-react';
import type { Task } from '../../types';
import { StatusBadge } from '../common/StatusBadge';
import { PriorityBadge } from '../common/PriorityBadge';
import { formatTimeAgo } from '../../utils/formatters';

interface TaskCardProps {
  task: Task;
  onCallNow?: (taskId: number) => void;
  onMarkComplete?: (taskId: number) => void;
}

export const TaskCard = ({ task, onCallNow, onMarkComplete }: TaskCardProps) => {
  return (
    <div className="bg-white shadow rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <h3 className="text-lg font-medium text-gray-900">{task.title}</h3>
          <p className="text-sm text-gray-500 mt-1">{task.contact_name} • {task.contact_phone}</p>
        </div>
        <div className="flex space-x-2">
          <StatusBadge status={task.status} />
          <PriorityBadge priority={task.priority} />
        </div>
      </div>

      <p className="text-sm text-gray-600 mb-3">{task.description}</p>

      <div className="flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center">
          <Clock className="h-4 w-4 mr-1" />
          {formatTimeAgo(task.created_at)}
        </div>
        <div className="flex items-center">
          <span className="mr-1">By:</span>
          <span className="font-medium">{task.created_by}</span>
        </div>
      </div>

      {task.status === 'pending' && (
        <div className="mt-4 flex space-x-2">
          {onCallNow && (
            <button
              onClick={() => onCallNow(task.id)}
              className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <Phone className="h-4 w-4 mr-1" />
              Call Now
            </button>
          )}
          {onMarkComplete && (
            <button
              onClick={() => onMarkComplete(task.id)}
              className="inline-flex items-center justify-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <CheckCircle className="h-4 w-4 mr-1" />
              Mark Done
            </button>
          )}
        </div>
      )}

      {task.contact_response && (
        <div className="mt-3 p-3 bg-gray-50 rounded-md">
          <p className="text-xs font-medium text-gray-700 mb-1">Response:</p>
          <p className="text-sm text-gray-600">{task.contact_response}</p>
        </div>
      )}
    </div>
  );
};
