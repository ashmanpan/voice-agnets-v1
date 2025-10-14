"""
Call Analysis Service - Analyzes call transcripts using AI
Enhanced with auto-extraction of reactive action items (Type 2)
"""
import json
from groq import Groq
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Call, CallAnalysis, TranscriptSegment, ActionItem, Contact


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

        # AUTO-EXTRACT: Create reactive action items (Type 2)
        self._create_action_items(call, analysis_data, db)

        return analysis if existing else db.query(CallAnalysis).filter(CallAnalysis.call_id == call.id).first()

    def _build_conversation_text(self, segments):
        """Build a readable conversation from transcript segments"""
        lines = []
        for seg in segments:
            speaker_label = "Agent" if seg.speaker == "agent" else "User"
            lines.append(f"{speaker_label}: {seg.text}")
        return "\n".join(lines)

    def _create_action_items(self, call: Call, analysis_data: dict, db: Session):
        """
        Create ActionItem records (Type 2) from extracted data
        Auto-generates reactive action items from conversation analysis
        """
        contact = db.query(Contact).filter(Contact.id == call.contact_id).first()
        if not contact:
            return

        # Determine which items to create action items for
        items_to_track = []

        # Add requests
        for request in analysis_data.get('requests', []):
            items_to_track.append({
                'type': 'request',
                'description': request,
                'priority': 'high',
                'urgency_score': 70
            })

        # Add complaints (highest priority)
        for complaint in analysis_data.get('complaints', []):
            items_to_track.append({
                'type': 'complaint',
                'description': complaint,
                'priority': 'high',
                'urgency_score': 85
            })

        # Add action items if they require follow-up
        for action in analysis_data.get('action_items', []):
            # Only create action items for user-requested actions
            if any(keyword in action.lower() for keyword in ['need', 'want', 'could', 'please', 'help', 'fix', 'check']):
                items_to_track.append({
                    'type': 'follow_up',
                    'description': action,
                    'priority': 'medium',
                    'urgency_score': 60
                })

        # Adjust urgency based on sentiment
        sentiment = analysis_data.get('sentiment', 'neutral')
        sentiment_boost = {
            'negative': 20,
            'neutral': 0,
            'positive': -10
        }
        boost = sentiment_boost.get(sentiment, 0)

        # Create action items
        for item in items_to_track:
            # Calculate due date (high priority = 2 days, medium = 5 days, low = 7 days)
            due_days = {'high': 2, 'medium': 5, 'low': 7}
            due_date = datetime.utcnow() + timedelta(days=due_days.get(item['priority'], 5))

            action_item = ActionItem(
                call_id=call.id,
                contact_id=call.contact_id,
                action_type=item['type'],
                description=item['description'],
                priority=item['priority'],
                status='pending',
                urgency_score=min(100, item['urgency_score'] + boost),
                assigned_to='CTO Office',
                due_date=due_date,
                source_text=item['description'][:500]  # Store first 500 chars as source
            )
            db.add(action_item)

        db.commit()
        print(f"✅ Created {len(items_to_track)} action items from call {call.id}")

    def _ai_analyze(self, conversation: str) -> dict:
        """Use AI to analyze the conversation"""

        prompt = f"""Analyze this phone conversation and provide a structured analysis in JSON format.

Conversation:
{conversation}

Provide your analysis as a JSON object with these fields:
- summary: A brief 1-2 sentence summary of the call
- action_items: Array of action items mentioned (things that need to be done)
- requests: Array of specific requests made by the user (things they asked for)
- complaints: Array of complaints or issues raised by the user
- sentiment: Overall sentiment (positive/neutral/negative)
- call_outcome: The outcome (answered/voicemail/no_answer/busy)

IMPORTANT:
- "requests" = things the user explicitly asked for or requested
- "complaints" = problems, issues, or dissatisfaction expressed by the user
- "action_items" = general things that need to be done

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
