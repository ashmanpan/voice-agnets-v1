import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ListTodo, AlertTriangle } from 'lucide-react';
import { tasksApi } from '../api/tasks';
import { actionsApi } from '../api/actions';
import { TaskCard } from '../components/actions/TaskCard';
import { ActionCard } from '../components/actions/ActionCard';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

export const Actions = () => {
  const [activeTab, setActiveTab] = useState<'tasks' | 'actions'>('tasks');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const queryClient = useQueryClient();

  // Fetch tasks
  const { data: tasksData, isLoading: tasksLoading } = useQuery({
    queryKey: ['tasks', { status: statusFilter === 'all' ? undefined : statusFilter }],
    queryFn: () => tasksApi.getTasks(statusFilter === 'all' ? {} : { status: statusFilter }),
  });

  // Fetch actions
  const { data: actionsData, isLoading: actionsLoading } = useQuery({
    queryKey: ['actions', { status: statusFilter === 'all' ? undefined : statusFilter }],
    queryFn: () => actionsApi.getActions(statusFilter === 'all' ? {} : { status: statusFilter }),
  });

  // Mutation to call a task
  const callTaskMutation = useMutation({
    mutationFn: (taskId: number) => tasksApi.initiateTaskCall(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      alert('Task call initiated!');
    },
  });

  // Mutation to update task status
  const updateTaskMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<any> }) =>
      tasksApi.updateTask(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  // Mutation to update action status
  const updateActionMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<any> }) =>
      actionsApi.updateAction(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['actions'] });
    },
  });

  const handleCallNow = (taskId: number) => {
    if (confirm('Initiate task delivery call now?')) {
      callTaskMutation.mutate(taskId);
    }
  };

  const handleMarkTaskComplete = (taskId: number) => {
    updateTaskMutation.mutate({ id: taskId, data: { status: 'completed' } });
  };

  const handleMarkActionComplete = (actionId: number) => {
    updateActionMutation.mutate({ id: actionId, data: { status: 'completed' } });
  };

  const tasks = tasksData?.tasks || [];
  const actions = actionsData?.actions || [];

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Actions & Tasks</h1>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('tasks')}
            className={`${
              activeTab === 'tasks'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center`}
          >
            <ListTodo className="h-5 w-5 mr-2" />
            Type 1: Tasks ({tasks.length})
          </button>
          <button
            onClick={() => setActiveTab('actions')}
            className={`${
              activeTab === 'actions'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center`}
          >
            <AlertTriangle className="h-5 w-5 mr-2" />
            Type 2: Actions ({actions.length})
          </button>
        </nav>
      </div>

      {/* Filters */}
      <div className="mb-6">
        <div className="flex items-center space-x-4">
          <label className="text-sm font-medium text-gray-700">Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="block px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          >
            <option value="all">All</option>
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
          </select>
        </div>
      </div>

      {/* Content */}
      {activeTab === 'tasks' ? (
        tasksLoading ? (
          <LoadingSpinner />
        ) : tasks.length === 0 ? (
          <div className="text-center py-12">
            <ListTodo className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No tasks</h3>
            <p className="mt-1 text-sm text-gray-500">No tasks found with the selected filters.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {tasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                onCallNow={handleCallNow}
                onMarkComplete={handleMarkTaskComplete}
              />
            ))}
          </div>
        )
      ) : actionsLoading ? (
        <LoadingSpinner />
      ) : actions.length === 0 ? (
        <div className="text-center py-12">
          <AlertTriangle className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No actions</h3>
          <p className="mt-1 text-sm text-gray-500">No actions found with the selected filters.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {actions.map((action) => (
            <ActionCard
              key={action.id}
              action={action}
              onMarkComplete={handleMarkActionComplete}
            />
          ))}
        </div>
      )}
    </div>
  );
};
