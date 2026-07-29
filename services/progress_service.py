from datetime import datetime
from services.database_service import get_connection

def get_completed(employee_id):
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT milestone_id FROM milestone_completion WHERE employee_id=? AND completed=1",
            (employee_id,)
        ).fetchall()
        return {row["milestone_id"] for row in rows}

def set_completion(employee_id, milestone_id, completed):
    with get_connection() as connection:
        connection.execute(
            '''
            INSERT INTO milestone_completion(employee_id,milestone_id,completed,completed_at)
            VALUES(?,?,?,?)
            ON CONFLICT(employee_id,milestone_id) DO UPDATE SET
                completed=excluded.completed,
                completed_at=excluded.completed_at
            ''',
            (
                employee_id,
                milestone_id,
                1 if completed else 0,
                datetime.now().isoformat(timespec="seconds") if completed else None
            )
        )

def calculate_score(employee_id, milestones):
    completed = get_completed(employee_id)
    total = sum(item["weight"] for item in milestones)
    achieved = sum(item["weight"] for item in milestones if item["id"] in completed)
    return round((achieved / total) * 100) if total else 0
