from services.database_service import get_connection

def list_employees():
    with get_connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM employees ORDER BY name"
        ).fetchall()]

def get_employee(employee_id):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM employees WHERE id=?", (employee_id,)
        ).fetchone()
        return dict(row) if row else None

def create_employee(data):
    with get_connection() as connection:
        cursor = connection.execute(
            '''
            INSERT INTO employees
            (employee_code,name,email,role,department,manager_name,mentor_name,
             location,experience_level,joining_date,onboarding_day)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            ''',
            (
                data["employee_code"], data["name"], data.get("email"),
                data.get("role","Business Analyst"), data.get("department"),
                data.get("manager_name"), data.get("mentor_name"), data.get("location"),
                data.get("experience_level"), data.get("joining_date"),
                int(data.get("onboarding_day",1))
            )
        )
        employee_id = cursor.lastrowid
    return get_employee(employee_id)

def update_employee(employee_id, data):
    with get_connection() as connection:
        connection.execute(
            '''
            UPDATE employees SET
                name=?,email=?,role=?,department=?,manager_name=?,mentor_name=?,
                location=?,experience_level=?,joining_date=?,onboarding_day=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            ''',
            (
                data["name"],data.get("email"),data.get("role"),data.get("department"),
                data.get("manager_name"),data.get("mentor_name"),data.get("location"),
                data.get("experience_level"),data.get("joining_date"),
                int(data.get("onboarding_day",1)),employee_id
            )
        )
    return get_employee(employee_id)
