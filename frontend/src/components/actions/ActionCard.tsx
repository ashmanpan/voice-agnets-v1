import { AlertCircle, CheckCircle } from 'lucide-react';
import type { ActionItem } from '../../types';
import { StatusBadge } from '../common/StatusBadge';
import { PriorityBadge } from '../common/PriorityBadge';
import { formatTimeAgo } from '../../utils/formatters';

interface ActionCardProps {
  action: ActionItem;
  onMarkComplete?: (actionId: number) => void;
}

export const ActionCard = ({ action, onMarkComplete }: ActionCardProps) => {
  return (
    <div className="bg-white shadow rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-orange-500 mr-2" />
            <h3 className="text-lg font-medium text-gray-900 capitalize">{action.action_type}</h3>
          </div>
          {action.contact_name && (
            <p className="text-sm text-gray-500 mt-1">{action.contact_name}</p>
          )}
        </div>
        <div className="flex space-x-2">
          <StatusBadge status={action.status} />
          <PriorityBadge priority={action.priority} />
        </div>
      </div>

      <p className="text-sm text-gray-600 mb-3">{action.description}</p>

      <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
        <div className="flex items-center">
          <span>Created {formatTimeAgo(action.created_at)}</span>
        </div>
        <div className="flex items-center">
          <span className="mr-1">Urgency:</span>
          <span className="font-medium">{action.urgency_score}/100</span>
        </div>
      </div>

      {action.status === 'pending' && onMarkComplete && (
        <button
          onClick={() => onMarkComplete(action.id)}
          className="w-full inline-flex items-center justify-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
        >
          <CheckCircle className="h-4 w-4 mr-1" />
          Mark Complete
        </button>
      )}

      {action.source_text && (
        <div className="mt-3 p-3 bg-gray-50 rounded-md">
          <p className="text-xs font-medium text-gray-700 mb-1">From Transcript:</p>
          <p className="text-sm text-gray-600 italic">"{action.source_text}"</p>
        </div>
      )}
    </div>
  );
};
