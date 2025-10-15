import { useQuery } from '@tanstack/react-query';
import { Phone, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { callsApi } from '../api/calls';
import { tasksApi } from '../api/tasks';
import { actionsApi } from '../api/actions';
import { StatsCard } from '../components/dashboard/StatsCard';
import { CallsTable } from '../components/dashboard/CallsTable';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

export const Dashboard = () => {
  // Fetch calls
  const { data: callsData, isLoading: callsLoading } = useQuery({
    queryKey: ['calls', { limit: 20 }],
    queryFn: () => callsApi.getCalls({ limit: 20 }),
  });

  // Fetch tasks
  const { data: tasksData } = useQuery({
    queryKey: ['tasks', { status: 'pending' }],
    queryFn: () => tasksApi.getTasks({ status: 'pending' }),
  });

  // Fetch actions
  const { data: actionsData } = useQuery({
    queryKey: ['actions', { status: 'pending' }],
    queryFn: () => actionsApi.getActions({ status: 'pending' }),
  });

  if (callsLoading) {
    return <LoadingSpinner />;
  }

  const calls = callsData?.calls || [];
  const totalCalls = callsData?.count || 0;
  const completedCalls = calls.filter(c => c.status === 'completed').length;
  const successRate = totalCalls > 0 ? ((completedCalls / totalCalls) * 100).toFixed(1) : '0';
  const pendingTasks = tasksData?.count || 0;
  const pendingActions = actionsData?.count || 0;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <StatsCard
          title="Total Calls"
          value={totalCalls}
          icon={Phone}
          color="bg-blue-500"
        />
        <StatsCard
          title="Success Rate"
          value={`${successRate}%`}
          icon={CheckCircle}
          color="bg-green-500"
        />
        <StatsCard
          title="Pending Tasks"
          value={pendingTasks}
          icon={Clock}
          color="bg-yellow-500"
        />
        <StatsCard
          title="Pending Actions"
          value={pendingActions}
          icon={AlertCircle}
          color="bg-orange-500"
        />
      </div>

      {/* Recent Calls Table */}
      <CallsTable calls={calls} />
    </div>
  );
};
