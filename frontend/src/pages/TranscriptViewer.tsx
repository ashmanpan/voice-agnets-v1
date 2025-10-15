import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Phone } from 'lucide-react';
import { callsApi } from '../api/calls';
import { MessageBubble } from '../components/transcript/MessageBubble';
import { AnalysisPanel } from '../components/transcript/AnalysisPanel';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { formatDateTime, formatDuration } from '../utils/formatters';

export const TranscriptViewer = () => {
  const { id } = useParams<{ id: string }>();
  const callId = Number(id);

  const { data: call, isLoading: callLoading } = useQuery({
    queryKey: ['call', callId],
    queryFn: () => callsApi.getCallById(callId),
  });

  const { data: transcriptData } = useQuery({
    queryKey: ['transcript', callId],
    queryFn: () => callsApi.getCallTranscript(callId),
    enabled: !!call,
  });

  const { data: analysisData } = useQuery({
    queryKey: ['analysis', callId],
    queryFn: () => callsApi.getCallAnalysis(callId),
    enabled: !!call,
  });

  if (callLoading) {
    return <LoadingSpinner />;
  }

  if (!call) {
    return (
      <div className="p-6">
        <p className="text-gray-500">Call not found.</p>
      </div>
    );
  }

  const transcript = transcriptData?.transcript || [];
  const analysis = analysisData?.analysis || null;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <Link
          to="/"
          className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Dashboard
        </Link>

        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center">
              <Phone className="h-8 w-8 text-blue-600 mr-4" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Call #{call.id}
                </h1>
                <p className="text-sm text-gray-500 mt-1">
                  {call.contact_name} • {call.contact_phone}
                </p>
              </div>
            </div>
            <StatusBadge status={call.status} />
          </div>

          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-500">Type</p>
              <p className="text-sm font-medium text-gray-900">{call.call_type}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Duration</p>
              <p className="text-sm font-medium text-gray-900">
                {formatDuration(call.duration_seconds)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Started</p>
              <p className="text-sm font-medium text-gray-900">
                {call.started_at ? formatDateTime(call.started_at) : 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Direction</p>
              <p className="text-sm font-medium text-gray-900">{call.direction}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Transcript */}
        <div className="lg:col-span-2">
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Transcript</h2>
            <div className="space-y-4 max-h-[600px] overflow-y-auto">
              {transcript.length === 0 ? (
                <p className="text-gray-500 text-sm">No transcript available.</p>
              ) : (
                transcript.map((segment) => (
                  <MessageBubble key={segment.id} segment={segment} />
                ))
              )}
            </div>
          </div>
        </div>

        {/* Analysis Panel */}
        <div className="lg:col-span-1">
          <AnalysisPanel analysis={analysis} />
        </div>
      </div>
    </div>
  );
};
