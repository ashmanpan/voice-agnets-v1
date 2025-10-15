import { MessageSquare, TrendingUp } from 'lucide-react';
import type { CallAnalysis } from '../../types';
import { getSentimentColor } from '../../utils/colors';

interface AnalysisPanelProps {
  analysis: CallAnalysis | null;
}

export const AnalysisPanel = ({ analysis }: AnalysisPanelProps) => {
  if (!analysis) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <MessageSquare className="h-5 w-5 mr-2" />
          AI Analysis
        </h3>
        <p className="text-gray-500 text-sm">Analysis not available for this call.</p>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <MessageSquare className="h-5 w-5 mr-2" />
        AI Analysis
      </h3>

      {/* Summary */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Summary</h4>
        <p className="text-sm text-gray-600">{analysis.summary}</p>
      </div>

      {/* Sentiment */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
          <TrendingUp className="h-4 w-4 mr-1" />
          Sentiment
        </h4>
        <span className={`text-sm font-medium ${getSentimentColor(analysis.sentiment)}`}>
          {analysis.sentiment.toUpperCase()}
        </span>
      </div>

      {/* Call Outcome */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Outcome</h4>
        <p className="text-sm text-gray-600">{analysis.call_outcome || 'N/A'}</p>
      </div>

      {/* Action Items */}
      {analysis.action_items && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Action Items</h4>
          <p className="text-sm text-gray-600">{analysis.action_items}</p>
        </div>
      )}

      {/* Requests */}
      {analysis.requests && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Requests</h4>
          <p className="text-sm text-gray-600">{analysis.requests}</p>
        </div>
      )}

      {/* Complaints */}
      {analysis.complaints && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Complaints</h4>
          <p className="text-sm text-gray-600">{analysis.complaints}</p>
        </div>
      )}
    </div>
  );
};
