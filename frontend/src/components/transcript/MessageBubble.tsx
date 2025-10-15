import { Bot, User } from 'lucide-react';
import type { TranscriptSegment } from '../../types';

interface MessageBubbleProps {
  segment: TranscriptSegment;
}

export const MessageBubble = ({ segment }: MessageBubbleProps) => {
  const isAgent = segment.speaker === 'agent';

  return (
    <div className={`flex ${isAgent ? 'justify-start' : 'justify-end'} mb-4`}>
      <div className={`flex max-w-3xl ${isAgent ? 'flex-row' : 'flex-row-reverse'}`}>
        <div className={`flex-shrink-0 ${isAgent ? 'mr-3' : 'ml-3'}`}>
          <div className={`h-8 w-8 rounded-full flex items-center justify-center ${
            isAgent ? 'bg-blue-100' : 'bg-gray-100'
          }`}>
            {isAgent ? (
              <Bot className="h-5 w-5 text-blue-600" />
            ) : (
              <User className="h-5 w-5 text-gray-600" />
            )}
          </div>
        </div>
        <div>
          <div className={`px-4 py-2 rounded-lg ${
            isAgent ? 'bg-blue-50 text-gray-900' : 'bg-gray-100 text-gray-900'
          }`}>
            <p className="text-sm">{segment.text}</p>
          </div>
        </div>
      </div>
    </div>
  );
};
