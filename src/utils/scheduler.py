import threading
import time
from datetime import datetime, timedelta

def cleanup_old_logs(app, db, ChatLog):
    """Delete chat logs older than 7 days"""
    with app.app_context():
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            old_logs = ChatLog.query.filter(ChatLog.created_at < cutoff_date).all()
            count = len(old_logs)
            for log in old_logs:
                db.session.delete(log)
            db.session.commit()
            print(f"[SCHEDULER] Cleaned up {count} old chat logs")
        except Exception as e:
            print(f"[SCHEDULER] Error cleaning up logs: {e}")
            db.session.rollback()

def start_scheduler(app, db, ChatLog):
    """Start the background scheduler for cleanup tasks"""
    def run_scheduler():
        while True:
            # Calculate seconds until midnight UTC
            now = datetime.utcnow()
            tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            sleep_seconds = (tomorrow - now).total_seconds()

            print(f"[SCHEDULER] Next cleanup scheduled in {sleep_seconds/3600:.2f} hours")
            time.sleep(sleep_seconds)

            cleanup_old_logs(app, db, ChatLog)

    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("[SCHEDULER] Background scheduler started")
