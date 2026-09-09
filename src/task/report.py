from datetime import datetime, timezone
from pathlib import Path

REPORT_FILE = Path(__file__).parent.parent.parent / "completion_reports.log"


def log_completion_report(
    task_id: int,
    title: str,
    user_id: str,
    completed_at: datetime,
) -> None:
    # completed_at = completed_at.astimezone(timezone.utc)
    line = (
        f"[{completed_at.isoformat()}] "
        f'TASK {task_id} DONE - "{title}" (owner: {user_id})\n'
    )
    with REPORT_FILE.open("a") as f:
        f.write(line)
