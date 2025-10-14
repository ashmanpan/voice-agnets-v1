"""
Daily Report Generator - Creates comprehensive reports of all calls
"""
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Call, Contact, CallAnalysis, TranscriptSegment


class DailyReportGenerator:
    def __init__(self, db: Session):
        self.db = db

    def generate_report(self, date: datetime = None) -> dict:
        """
        Generate a comprehensive daily report
        If date is None, generates report for today
        """
        if date is None:
            date = datetime.utcnow().date()
        else:
            date = date.date() if isinstance(date, datetime) else date

        start_time = datetime.combine(date, datetime.min.time())
        end_time = datetime.combine(date, datetime.max.time())

        # Get all calls for the day
        calls = self.db.query(Call).filter(
            Call.created_at >= start_time,
            Call.created_at <= end_time
        ).all()

        # Overall statistics
        total_calls = len(calls)
        completed_calls = len([c for c in calls if c.status == 'completed'])
        failed_calls = len([c for c in calls if c.status in ['failed', 'busy', 'no-answer']])
        in_progress = len([c for c in calls if c.status == 'in-progress'])

        total_duration = sum([c.duration or 0 for c in calls])
        avg_duration = total_duration / completed_calls if completed_calls > 0 else 0

        # Analyze calls with AI analysis
        analyzed_calls = []
        all_action_items = []
        all_requests = []
        all_complaints = []
        sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
        outcome_counts = {}

        for call in calls:
            analysis = self.db.query(CallAnalysis).filter(
                CallAnalysis.call_id == call.id
            ).first()

            if analysis:
                contact = call.contact

                # Parse JSON fields
                action_items = json.loads(analysis.action_items) if analysis.action_items else []
                requests = json.loads(analysis.requests) if analysis.requests else []
                complaints = json.loads(analysis.complaints) if analysis.complaints else []

                call_data = {
                    'call_id': call.id,
                    'contact_name': contact.name if contact else 'Unknown',
                    'phone_number': contact.phone_number if contact else 'Unknown',
                    'duration': call.duration,
                    'status': call.status,
                    'summary': analysis.summary,
                    'action_items': action_items,
                    'requests': requests,
                    'complaints': complaints,
                    'sentiment': analysis.sentiment,
                    'call_outcome': analysis.call_outcome,
                    'created_at': call.created_at.isoformat()
                }

                analyzed_calls.append(call_data)

                # Aggregate data
                all_action_items.extend(action_items)
                all_requests.extend(requests)
                all_complaints.extend(complaints)

                sentiment_counts[analysis.sentiment] = sentiment_counts.get(analysis.sentiment, 0) + 1
                outcome_counts[analysis.call_outcome] = outcome_counts.get(analysis.call_outcome, 0) + 1

        # Build report
        report = {
            'report_date': date.isoformat(),
            'generated_at': datetime.utcnow().isoformat(),
            'statistics': {
                'total_calls': total_calls,
                'completed_calls': completed_calls,
                'failed_calls': failed_calls,
                'in_progress_calls': in_progress,
                'total_duration_seconds': total_duration,
                'average_duration_seconds': round(avg_duration, 2),
                'sentiment_distribution': sentiment_counts,
                'outcome_distribution': outcome_counts
            },
            'aggregated_insights': {
                'total_action_items': len(all_action_items),
                'action_items': all_action_items,
                'total_requests': len(all_requests),
                'requests': all_requests,
                'total_complaints': len(all_complaints),
                'complaints': all_complaints
            },
            'calls': analyzed_calls
        }

        return report

    def generate_text_report(self, date: datetime = None) -> str:
        """Generate a human-readable text version of the report"""
        report = self.generate_report(date)

        lines = []
        lines.append("=" * 80)
        lines.append(f"📊 DAILY CALL REPORT - {report['report_date']}")
        lines.append(f"Generated at: {report['generated_at']}")
        lines.append("=" * 80)
        lines.append("")

        # Statistics
        stats = report['statistics']
        lines.append("📈 STATISTICS")
        lines.append("-" * 80)
        lines.append(f"Total Calls:         {stats['total_calls']}")
        lines.append(f"Completed:           {stats['completed_calls']}")
        lines.append(f"Failed/No Answer:    {stats['failed_calls']}")
        lines.append(f"In Progress:         {stats['in_progress_calls']}")
        lines.append(f"Total Duration:      {stats['total_duration_seconds']}s ({stats['total_duration_seconds']//60} min)")
        lines.append(f"Average Duration:    {stats['average_duration_seconds']}s")
        lines.append("")

        # Sentiment
        lines.append("😊 SENTIMENT DISTRIBUTION")
        lines.append("-" * 80)
        for sentiment, count in stats['sentiment_distribution'].items():
            lines.append(f"{sentiment.capitalize()}: {count}")
        lines.append("")

        # Outcomes
        lines.append("📞 CALL OUTCOMES")
        lines.append("-" * 80)
        for outcome, count in stats['outcome_distribution'].items():
            lines.append(f"{outcome}: {count}")
        lines.append("")

        # Aggregated Insights
        insights = report['aggregated_insights']
        lines.append("💡 AGGREGATED INSIGHTS")
        lines.append("-" * 80)
        lines.append(f"Total Action Items: {insights['total_action_items']}")
        if insights['action_items']:
            for item in insights['action_items']:
                lines.append(f"  • {item}")
        lines.append("")

        lines.append(f"Total Requests: {insights['total_requests']}")
        if insights['requests']:
            for req in insights['requests']:
                lines.append(f"  • {req}")
        lines.append("")

        lines.append(f"Total Complaints: {insights['total_complaints']}")
        if insights['complaints']:
            for complaint in insights['complaints']:
                lines.append(f"  ⚠️  {complaint}")
        lines.append("")

        # Individual Calls
        lines.append("📋 INDIVIDUAL CALL DETAILS")
        lines.append("=" * 80)
        for call in report['calls']:
            lines.append("")
            lines.append(f"Call #{call['call_id']} - {call['contact_name']} ({call['phone_number']})")
            lines.append(f"Status: {call['status']} | Duration: {call['duration']}s | Outcome: {call['call_outcome']}")
            lines.append(f"Sentiment: {call['sentiment']}")
            lines.append(f"Summary: {call['summary']}")

            if call['action_items']:
                lines.append("Action Items:")
                for item in call['action_items']:
                    lines.append(f"  • {item}")

            if call['requests']:
                lines.append("Requests:")
                for req in call['requests']:
                    lines.append(f"  • {req}")

            if call['complaints']:
                lines.append("Complaints:")
                for complaint in call['complaints']:
                    lines.append(f"  ⚠️  {complaint}")

            lines.append("-" * 80)

        lines.append("")
        lines.append("=" * 80)
        lines.append("End of Report")
        lines.append("=" * 80)

        return "\n".join(lines)

    def generate_summary_report(self, days: int = 7) -> dict:
        """Generate a summary report for the last N days"""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)

        start_time = datetime.combine(start_date, datetime.min.time())
        end_time = datetime.combine(end_date, datetime.max.time())

        calls = self.db.query(Call).filter(
            Call.created_at >= start_time,
            Call.created_at <= end_time
        ).all()

        # Daily breakdown
        daily_stats = {}
        for call in calls:
            call_date = call.created_at.date().isoformat()
            if call_date not in daily_stats:
                daily_stats[call_date] = {
                    'total': 0,
                    'completed': 0,
                    'failed': 0
                }

            daily_stats[call_date]['total'] += 1
            if call.status == 'completed':
                daily_stats[call_date]['completed'] += 1
            elif call.status in ['failed', 'busy', 'no-answer']:
                daily_stats[call_date]['failed'] += 1

        return {
            'period': f'{start_date} to {end_date}',
            'days': days,
            'total_calls': len(calls),
            'daily_breakdown': daily_stats
        }
