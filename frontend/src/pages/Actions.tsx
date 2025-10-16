import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ListTodo, AlertTriangle, CheckSquare, Square, Trash2, CheckCircle } from 'lucide-react';
import { tasksApi } from '../api/tasks';
import { actionsApi } from '../api/actions';
import { TaskCard } from '../components/actions/TaskCard';
import { ActionCard } from '../components/actions/ActionCard';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

export const Actions = () => {
  const [activeTab, setActiveTab] = useState<'tasks' | 'actions'>('tasks');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedTasks, setSelectedTasks] = useState<number[]>([]);
  const [selectedActions, setSelectedActions] = useState<number[]>([]);
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

  // Bulk operations handlers
  const handleSelectAll = () => {
    if (activeTab === 'tasks') {
      if (selectedTasks.length === tasks.length) {
        setSelectedTasks([]);
      } else {
        setSelectedTasks(tasks.map(t => t.id));
      }
    } else {
      if (selectedActions.length === actions.length) {
        setSelectedActions([]);
      } else {
        setSelectedActions(actions.map(a => a.id));
      }
    }
  };

  const handleToggleSelect = (id: number) => {
    if (activeTab === 'tasks') {
      setSelectedTasks(prev =>
        prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
      );
    } else {
      setSelectedActions(prev =>
        prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
      );
    }
  };

  const handleBulkComplete = async () => {
    const items = activeTab === 'tasks' ? selectedTasks : selectedActions;
    if (items.length === 0) return;

    if (confirm(`Mark ${items.length} ${activeTab} as completed?`)) {
      for (const id of items) {
        if (activeTab === 'tasks') {
          await tasksApi.updateTask(id, { status: 'completed' });
        } else {
          await actionsApi.updateAction(id, { status: 'completed' });
        }
      }
      queryClient.invalidateQueries({ queryKey: [activeTab] });
      activeTab === 'tasks' ? setSelectedTasks([]) : setSelectedActions([]);
    }
  };

  const handleBulkDelete = async () => {
    const items = activeTab === 'tasks' ? selectedTasks : selectedActions;
    if (items.length === 0) return;

    if (confirm(`Delete ${items.length} ${activeTab}? This action cannot be undone.`)) {
      // Note: Delete functionality would need to be implemented in the backend
      alert('Bulk delete is not yet implemented in the backend');
    }
  };

  const tasks = tasksData?.tasks || [];
  const actions = actionsData?.actions || [];
  const selectedCount = activeTab === 'tasks' ? selectedTasks.length : selectedActions.length;

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

      {/* Filters and Bulk Operations Bar */}
      <div className="mb-6 space-y-4">
        <div className="flex items-center justify-between">
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

          <button
            onClick={handleSelectAll}
            className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            {selectedCount > 0 ? (
              <>
                <CheckSquare className="h-4 w-4 mr-2" />
                Deselect All
              </>
            ) : (
              <>
                <Square className="h-4 w-4 mr-2" />
                Select All
              </>
            )}
          </button>
        </div>

        {/* Bulk Operations Bar */}
        {selectedCount > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-center justify-between">
            <span className="text-sm font-medium text-blue-900">
              {selectedCount} {activeTab} selected
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={handleBulkComplete}
                className="inline-flex items-center px-3 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700"
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Mark Complete
              </button>
              <button
                onClick={handleBulkDelete}
                className="inline-flex items-center px-3 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </button>
            </div>
          </div>
        )}
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
              <div key={task.id} className="relative">
                <div
                  className="absolute top-2 left-2 z-10 cursor-pointer"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleToggleSelect(task.id);
                  }}
                >
                  {selectedTasks.includes(task.id) ? (
                    <CheckSquare className="h-5 w-5 text-blue-600" />
                  ) : (
                    <Square className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                  )}
                </div>
                <TaskCard
                  key={task.id}
                  task={task}
                  onCallNow={handleCallNow}
                  onMarkComplete={handleMarkTaskComplete}
                />
              </div>
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
            <div key={action.id} className="relative">
              <div
                className="absolute top-2 left-2 z-10 cursor-pointer"
                onClick={(e) => {
                  e.stopPropagation();
                  handleToggleSelect(action.id);
                }}
              >
                {selectedActions.includes(action.id) ? (
                  <CheckSquare className="h-5 w-5 text-blue-600" />
                ) : (
                  <Square className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                )}
              </div>
              <ActionCard
                key={action.id}
                action={action}
                onMarkComplete={handleMarkActionComplete}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
