import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Calendar, List, Plus, Pause, Play, Trash2 } from 'lucide-react';
import { Calendar as BigCalendar, dateFnsLocalizer } from 'react-big-calendar';
import { format, parse, startOfWeek, getDay } from 'date-fns';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import { scheduleApi, type ScheduledCall } from '../api/schedule';

const locales = {
  'en-US': require('date-fns/locale/en-US'),
};

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales,
});

export const Schedule = () => {
  const [view, setView] = useState<'calendar' | 'list'>('calendar');
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const queryClient = useQueryClient();

  // Fetch scheduled calls
  const { data: scheduledCalls = [], isLoading: loadingScheduled } = useQuery({
    queryKey: ['scheduled-calls'],
    queryFn: scheduleApi.getScheduledCalls,
  });

  // Fetch recurring calls
  const { data: recurringCalls = [], isLoading: loadingRecurring } = useQuery({
    queryKey: ['recurring-calls'],
    queryFn: scheduleApi.getRecurringCalls,
  });

  // Mutations
  const pauseMutation = useMutation({
    mutationFn: scheduleApi.pauseRecurringCall,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recurring-calls'] });
    },
  });

  const resumeMutation = useMutation({
    mutationFn: scheduleApi.resumeRecurringCall,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recurring-calls'] });
    },
  });

  const cancelMutation = useMutation({
    mutationFn: scheduleApi.cancelCall,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-calls'] });
      queryClient.invalidateQueries({ queryKey: ['recurring-calls'] });
    },
  });

  // Transform scheduled calls for calendar
  const calendarEvents = scheduledCalls
    .filter(call => call.scheduled_time)
    .map(call => ({
      id: call.id,
      title: `${call.contact_name || 'Unknown'} - ${call.call_type}`,
      start: new Date(call.scheduled_time!),
      end: new Date(call.scheduled_time!),
      resource: call,
    }));

  const handlePauseResume = (call: ScheduledCall) => {
    if (call.is_active) {
      pauseMutation.mutate(call.id);
    } else {
      resumeMutation.mutate(call.id);
    }
  };

  const handleCancel = (callId: number) => {
    if (confirm('Are you sure you want to cancel this call?')) {
      cancelMutation.mutate(callId);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Call Schedule</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setView(view === 'calendar' ? 'list' : 'calendar')}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            {view === 'calendar' ? (
              <>
                <List className="h-4 w-4 mr-2" />
                List View
              </>
            ) : (
              <>
                <Calendar className="h-4 w-4 mr-2" />
                Calendar View
              </>
            )}
          </button>
          <button
            onClick={() => setShowScheduleModal(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="h-4 w-4 mr-2" />
            Schedule Call
          </button>
        </div>
      </div>

      {/* Calendar View */}
      {view === 'calendar' && (
        <div className="bg-white rounded-lg shadow p-6" style={{ height: '600px' }}>
          {loadingScheduled ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-gray-500">Loading schedule...</div>
            </div>
          ) : (
            <BigCalendar
              localizer={localizer}
              events={calendarEvents}
              startAccessor="start"
              endAccessor="end"
              style={{ height: '100%' }}
              views={['month', 'week', 'day']}
              onSelectEvent={(event) => {
                const call = event.resource as ScheduledCall;
                console.log('Selected call:', call);
              }}
            />
          )}
        </div>
      )}

      {/* List View */}
      {view === 'list' && (
        <div className="space-y-6">
          {/* Scheduled Calls Section */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">
                One-Time Scheduled Calls ({scheduledCalls.length})
              </h2>
            </div>
            <div className="px-6 py-4">
              {loadingScheduled ? (
                <div className="text-center text-gray-500 py-8">Loading...</div>
              ) : scheduledCalls.length === 0 ? (
                <div className="text-center text-gray-500 py-8">No scheduled calls</div>
              ) : (
                <div className="space-y-4">
                  {scheduledCalls.map(call => (
                    <div
                      key={call.id}
                      className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium text-gray-900">{call.contact_name}</h3>
                          <span className="text-sm text-gray-500">({call.contact_phone})</span>
                        </div>
                        <div className="mt-1 text-sm text-gray-600">
                          <span className="font-medium">{call.call_type}</span>
                          {call.scheduled_time && (
                            <span className="ml-2">
                              • Scheduled: {format(new Date(call.scheduled_time), 'PPp')}
                            </span>
                          )}
                        </div>
                        {call.custom_greeting && (
                          <p className="mt-1 text-sm text-gray-500 line-clamp-1">
                            {call.custom_greeting}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-2 py-1 text-xs rounded-full ${
                            call.status === 'scheduled'
                              ? 'bg-gray-100 text-gray-800'
                              : call.status === 'completed'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {call.status}
                        </span>
                        <button
                          onClick={() => handleCancel(call.id)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded-md"
                          title="Cancel call"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Recurring Calls Section */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">
                Recurring Calls ({recurringCalls.length})
              </h2>
            </div>
            <div className="px-6 py-4">
              {loadingRecurring ? (
                <div className="text-center text-gray-500 py-8">Loading...</div>
              ) : recurringCalls.length === 0 ? (
                <div className="text-center text-gray-500 py-8">No recurring calls</div>
              ) : (
                <div className="space-y-4">
                  {recurringCalls.map(call => (
                    <div
                      key={call.id}
                      className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium text-gray-900">{call.contact_name}</h3>
                          <span className="text-sm text-gray-500">({call.contact_phone})</span>
                        </div>
                        <div className="mt-1 text-sm text-gray-600">
                          <span className="font-medium">{call.call_type}</span>
                          <span className="ml-2">
                            • {call.recurrence_pattern}
                            {call.recurrence_day && ` on ${call.recurrence_day}`}
                            {call.recurrence_time && ` at ${call.recurrence_time}`}
                          </span>
                        </div>
                        {call.custom_greeting && (
                          <p className="mt-1 text-sm text-gray-500 line-clamp-1">
                            {call.custom_greeting}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-2 py-1 text-xs rounded-full ${
                            call.is_active
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {call.is_active ? 'Active' : 'Paused'}
                        </span>
                        <button
                          onClick={() => handlePauseResume(call)}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded-md"
                          title={call.is_active ? 'Pause' : 'Resume'}
                        >
                          {call.is_active ? (
                            <Pause className="h-4 w-4" />
                          ) : (
                            <Play className="h-4 w-4" />
                          )}
                        </button>
                        <button
                          onClick={() => handleCancel(call.id)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded-md"
                          title="Cancel recurring call"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
