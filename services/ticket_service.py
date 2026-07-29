from services.database_service import get_connection

VALID_STATUSES = ["Open","Assigned","In Progress","Waiting for Employee","Resolved","Closed"]

def create_ticket(employee_id, category, subject, description, priority="Medium"):
    with get_connection() as connection:
        cursor = connection.execute(
            '''
            INSERT INTO tickets(employee_id,category,subject,description,priority,status)
            VALUES(?,?,?,?,?,'Open')
            ''',
            (employee_id,category,subject,description,priority)
        )
        ticket_id = cursor.lastrowid
        number = f"ONB-{ticket_id:05d}"
        connection.execute("UPDATE tickets SET ticket_number=? WHERE id=?", (number,ticket_id))
        connection.execute(
            '''
            INSERT INTO ticket_history(ticket_id,old_status,new_status,comment)
            VALUES(?,NULL,'Open','Ticket created')
            ''',
            (ticket_id,)
        )
        return dict(connection.execute(
            "SELECT * FROM tickets WHERE id=?", (ticket_id,)
        ).fetchone())

def list_tickets(employee_id=None):
    with get_connection() as connection:
        if employee_id:
            rows = connection.execute(
                '''
                SELECT t.*, e.name employee_name
                FROM tickets t JOIN employees e ON e.id=t.employee_id
                WHERE t.employee_id=? ORDER BY t.created_at DESC
                ''',
                (employee_id,)
            ).fetchall()
        else:
            rows = connection.execute(
                '''
                SELECT t.*, e.name employee_name
                FROM tickets t JOIN employees e ON e.id=t.employee_id
                ORDER BY t.created_at DESC
                '''
            ).fetchall()
        return [dict(row) for row in rows]

def update_ticket(ticket_id,status,assigned_to=None,resolution=None,comment=""):
    if status not in VALID_STATUSES:
        raise ValueError("Invalid ticket status.")
    with get_connection() as connection:
        current = connection.execute(
            "SELECT * FROM tickets WHERE id=?", (ticket_id,)
        ).fetchone()
        if not current:
            raise ValueError("Ticket not found.")
        connection.execute(
            '''
            UPDATE tickets SET
                status=?,assigned_to=COALESCE(?,assigned_to),
                resolution=COALESCE(?,resolution),
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            ''',
            (status,assigned_to,resolution,ticket_id)
        )
        connection.execute(
            '''
            INSERT INTO ticket_history(ticket_id,old_status,new_status,comment)
            VALUES(?,?,?,?)
            ''',
            (ticket_id,current["status"],status,comment)
        )
        return dict(connection.execute(
            "SELECT * FROM tickets WHERE id=?", (ticket_id,)
        ).fetchone())

def ticket_history(ticket_id):
    with get_connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM ticket_history WHERE ticket_id=? ORDER BY changed_at DESC",
            (ticket_id,)
        ).fetchall()]
