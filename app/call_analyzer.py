"""
Call Analysis Service - Analyzes call transcripts using AI
"""
import json
from groq import Groq
import os
from sqlalchemy.orm import Session
from models import Call, CallAnalysis, TranscriptSegment


class CallAnalyzer:
    def __init__(self):
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"

    def analyze_call(self, call: Call, db: Session) -> CallAnalysis:
        """
        Analyze a completed call and extract insights
        """
        # Get transcript segments
        segments = db.query(TranscriptSegment).filter(
            TranscriptSegment.call_id == call.id
        ).order_by(TranscriptSegment.sequence_number).all()

        if not segments:
            return None

        # Build conversation text
        conversation = self._build_conversation_text(segments)

        # Use AI to analyze
        analysis_data = self._ai_analyze(conversation)

        # Create or update analysis record
        existing = db.query(CallAnalysis).filter(
            CallAnalysis.call_id == call.id
        ).first()

        if existing:
            # Update existing
            existing.summary = analysis_data['summary']
            existing.action_items = json.dumps(analysis_data['action_items'])
            existing.requests = json.dumps(analysis_data['requests'])
            existing.complaints = json.dumps(analysis_data['complaints'])
            existing.sentiment = analysis_data['sentiment']
            existing.call_outcome = analysis_data['call_outcome']
            db.commit()
            return existing
        else:
            # Create new
            analysis = CallAnalysis(
                call_id=call.id,
                summary=analysis_data['summary'],
                action_items=json.dumps(analysis_data['action_items']),
                requests=json.dumps(analysis_data['requests']),
                complaints=json.dumps(analysis_data['complaints']),
                sentiment=analysis_data['sentiment'],
                call_outcome=analysis_data['call_outcome']
            )
            db.add(analysis)
            db.commit()
            db.refresh(analysis)
            return analysis

    def _build_conversation_text(self, segments):
        """Build a readable conversation from transcript segments"""
        lines = []
        for seg in segments:
            speaker_label = "Agent" if seg.speaker == "agent" else "User"
            lines.append(f"{speaker_label}: {seg.text}")
        return "\n".join(lines)

    def _ai_analyze(self, conversation: str) -> dict:
        """Use AI to analyze the conversation"""

        prompt = f"""Analyze this phone conversation and provide a structured analysis in JSON format.

Conversation:
{conversation}

Provide your analysis as a JSON object with these fields:
- summary: A brief 1-2 sentence summary of the call
- action_items: Array of action items mentioned (things that need to be done)
- requests: Array of specific requests made by the user
- complaints: Array of complaints or issues raised
- sentiment: Overall sentiment (positive/neutral/negative)
- call_outcome: The outcome (answered/voicemail/no_answer/busy)

Return ONLY valid JSON, no other text.
"""

        try:
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing phone conversations. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )

            result_text = response.choices[0].message.content.strip()

            # Try to extract JSON if wrapped in code blocks
            if result_text.startswith("```"):
                # Remove code block markers
                result_text = result_text.split("```json")[-1].split("```")[0].strip()

            analysis = json.loads(result_text)

            # Ensure all required fields exist
            return {
                'summary': analysis.get('summary', 'No summary available'),
                'action_items': analysis.get('action_items', []),
                'requests': analysis.get('requests', []),
                'complaints': analysis.get('complaints', []),
                'sentiment': analysis.get('sentiment', 'neutral'),
                'call_outcome': analysis.get('call_outcome', 'unknown')
            }

        except Exception as e:
            print(f"Error analyzing call: {e}")
            # Return default analysis if AI fails
            return {
                'summary': 'Analysis failed',
                'action_items': [],
                'requests': [],
                'complaints': [],
                'sentiment': 'neutral',
                'call_outcome': 'unknown'
            }
