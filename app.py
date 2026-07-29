import json
import os
import streamlit as st

from config import GEMINI_MODEL, PLAN_FILE, POLICY_DIR, TOP_K
from services.database_service import initialize_database
from services.employee_service import list_employees, get_employee, create_employee, update_employee
from services.progress_service import get_completed, set_completion, calculate_score
from services.retrieval_service import PolicyRetriever
from services.generation_service import generate_answer
from services.sentiment_service import analyze_sentiment, save_feedback
from services.ticket_service import create_ticket, list_tickets, update_ticket, ticket_history, VALID_STATUSES

st.set_page_config(page_title="Aida — Employee Onboarding", page_icon="🧭", layout="wide")

@st.cache_resource
def load_retriever():
    return PolicyRetriever(POLICY_DIR)

@st.cache_data
def load_plan():
    return json.loads(PLAN_FILE.read_text(encoding="utf-8"))

initialize_database()
plan = load_plan()
retriever = load_retriever()
employees = list_employees()

if "employee_id" not in st.session_state:
    st.session_state.employee_id = employees[0]["id"] if employees else None

if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role":"assistant",
        "content":"Hi, I’m **Aida**. Ask me about onboarding policies, progress, or support."
    }]

if "ticket_seed" not in st.session_state:
    st.session_state.ticket_seed = ""

with st.sidebar:
    st.title("🧭 Aida")

    if employees:
        selected = st.selectbox(
            "Current employee",
            employees,
            index=next(
                (i for i,e in enumerate(employees) if e["id"] == st.session_state.employee_id),
                0
            ),
            format_func=lambda e: f"{e['employee_code']} — {e['name']}"
        )
        st.session_state.employee_id = selected["id"]

    api_key = os.getenv("GEMINI_API_KEY","") or st.text_input(
        "Gemini API key",
        type="password",
        help="Optional. The app works without Gemini."
    )

    employee = get_employee(st.session_state.employee_id) if st.session_state.employee_id else None

    if employee:
        st.divider()
        st.markdown(f"**{employee['name']}**")
        st.caption(f"{employee['role']} · Day {employee['onboarding_day']} of 30")

        completed = get_completed(employee["id"])
        score = calculate_score(employee["id"], plan["milestones"])

        st.progress(score/100, text=f"Onboarding score: {score}%")
        st.write(f"{len(completed)}/{len(plan['milestones'])} milestones completed")

tabs = st.tabs([
    "💬 Assistant",
    "👤 Employee Profile",
    "📋 Progress",
    "🎫 My Tickets",
    "🛠 Ticket Admin",
    "📚 Policy Library",
])

with tabs[0]:
    st.header("Conversational Onboarding Assistant")

    if not employee:
        st.warning("Add an employee profile first.")
    else:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                if message.get("sentiment"):
                    sentiment = message["sentiment"]
                    with st.expander("Sentiment analysis"):
                        st.write(f"{sentiment['label']} · score {sentiment['score']}")
                        st.write(sentiment["recommendation"])
                        if sentiment["urgent_terms"]:
                            st.warning("Urgent terms: " + ", ".join(sentiment["urgent_terms"]))

                if message.get("sources"):
                    with st.expander("Retrieved policy evidence"):
                        for result in message["sources"]:
                            policy = result["policy"]
                            st.markdown(
                                f"**{policy['id']} — {policy['title']}** "
                                f"· relevance `{result['score']:.3f}`"
                            )
                            st.write(policy["summary"])

        question = st.chat_input(
            "Ask a policy question or describe an onboarding issue..."
        )

        if question:
            st.session_state.messages.append({"role":"user","content":question})

            sentiment = analyze_sentiment(question)
            save_feedback(employee["id"], question, sentiment)

            results = retriever.search(question, TOP_K)
            score = calculate_score(employee["id"], plan["milestones"])

            answer, warning = generate_answer(
                question, results, api_key, GEMINI_MODEL, employee, score
            )

            if warning:
                answer += f"\n\n_ℹ️ {warning}_"

            st.session_state.messages.append({
                "role":"assistant",
                "content":answer,
                "sources":results,
                "sentiment":sentiment
            })

            if sentiment["needs_support"]:
                st.session_state.ticket_seed = question

            st.rerun()

        if st.session_state.ticket_seed:
            st.warning("This message may require additional support.")

            if st.button("Use message to create a ticket"):
                st.session_state.open_ticket_form = True

            if st.session_state.get("open_ticket_form"):
                with st.form("chat_ticket_form", clear_on_submit=True):
                    subject = st.text_input("Ticket subject", value="Onboarding support request")
                    category = st.selectbox(
                        "Category",
                        ["HR Policy","Training","Manager Support","Access Request","Data or Reporting","Workplace Concern","Other"]
                    )
                    priority = st.selectbox(
                        "Priority",
                        ["Low","Medium","High","Critical"],
                        index=2
                    )
                    description = st.text_area(
                        "Description",
                        value=st.session_state.ticket_seed
                    )

                    if st.form_submit_button("Create ticket"):
                        ticket = create_ticket(
                            employee["id"], category, subject, description, priority
                        )
                        st.success(f"Created {ticket['ticket_number']}")
                        st.session_state.ticket_seed = ""
                        st.session_state.open_ticket_form = False
                        st.rerun()

with tabs[1]:
    st.header("Employee Profiles")

    if employee:
        st.subheader("Edit current employee")

        with st.form("edit_employee_form"):
            name = st.text_input("Full name", value=employee["name"])
            email = st.text_input("Email", value=employee.get("email") or "")
            role = st.text_input("Role", value=employee.get("role") or "Business Analyst")
            department = st.text_input("Department", value=employee.get("department") or "")
            manager_name = st.text_input("Manager", value=employee.get("manager_name") or "")
            mentor_name = st.text_input("Mentor", value=employee.get("mentor_name") or "")
            location = st.text_input("Location", value=employee.get("location") or "")
            experience_level = st.selectbox(
                "Experience level",
                ["Graduate","Associate","Experienced","Senior"],
                index=["Graduate","Associate","Experienced","Senior"].index(
                    employee.get("experience_level")
                    if employee.get("experience_level") in ["Graduate","Associate","Experienced","Senior"]
                    else "Associate"
                )
            )
            joining_date = st.text_input(
                "Joining date",
                value=employee.get("joining_date") or ""
            )
            onboarding_day = st.number_input(
                "Onboarding day",
                1, 30,
                int(employee.get("onboarding_day") or 1)
            )

            if st.form_submit_button("Update employee"):
                update_employee(employee["id"], {
                    "name": name,
                    "email": email,
                    "role": role,
                    "department": department,
                    "manager_name": manager_name,
                    "mentor_name": mentor_name,
                    "location": location,
                    "experience_level": experience_level,
                    "joining_date": joining_date,
                    "onboarding_day": onboarding_day,
                })
                st.success("Employee updated.")
                st.rerun()

    st.divider()
    st.subheader("Add a new employee")

    with st.form("new_employee_form", clear_on_submit=True):
        employee_code = st.text_input("Employee code")
        name = st.text_input("Full name")
        email = st.text_input("Email")
        role = st.text_input("Role", value="Business Analyst")
        department = st.text_input("Department", value="Digital Transformation")
        manager_name = st.text_input("Manager")
        mentor_name = st.text_input("Mentor")
        location = st.text_input("Location")
        experience_level = st.selectbox(
            "Experience level",
            ["Graduate","Associate","Experienced","Senior"]
        )
        joining_date = st.date_input("Joining date")
        onboarding_day = st.number_input("Onboarding day", 1, 30, 1)

        if st.form_submit_button("Add employee"):
            if not employee_code.strip() or not name.strip():
                st.error("Employee code and name are required.")
            else:
                try:
                    new_employee = create_employee({
                        "employee_code": employee_code.strip(),
                        "name": name.strip(),
                        "email": email.strip(),
                        "role": role.strip(),
                        "department": department.strip(),
                        "manager_name": manager_name.strip(),
                        "mentor_name": mentor_name.strip(),
                        "location": location.strip(),
                        "experience_level": experience_level,
                        "joining_date": str(joining_date),
                        "onboarding_day": onboarding_day,
                    })
                    st.session_state.employee_id = new_employee["id"]
                    st.success("Employee created.")
                    st.rerun()
                except Exception as error:
                    st.error(f"Unable to create employee: {error}")

with tabs[2]:
    st.header("30-Day Onboarding Progress")

    if not employee:
        st.info("Select or create an employee.")
    else:
        completed = get_completed(employee["id"])

        for week in sorted({item["week"] for item in plan["milestones"]}):
            st.subheader(f"Week {week}")

            for milestone in [
                item for item in plan["milestones"]
                if item["week"] == week
            ]:
                is_complete = milestone["id"] in completed

                selected = st.checkbox(
                    f"Day {milestone['day']}: {milestone['title']}",
                    value=is_complete,
                    key=f"{employee['id']}_{milestone['id']}"
                )

                if selected != is_complete:
                    set_completion(
                        employee["id"],
                        milestone["id"],
                        selected
                    )
                    st.rerun()

with tabs[3]:
    st.header("My Support Tickets")

    if not employee:
        st.info("Select or create an employee.")
    else:
        with st.expander("Raise a new ticket"):
            with st.form("new_ticket_form", clear_on_submit=True):
                category = st.selectbox(
                    "Category",
                    ["HR Policy","Training","Manager Support","Access Request","Data or Reporting","Workplace Concern","Other"]
                )
                subject = st.text_input("Subject")
                description = st.text_area("Description")
                priority = st.selectbox(
                    "Priority",
                    ["Low","Medium","High","Critical"]
                )

                if st.form_submit_button("Create ticket"):
                    if not subject.strip() or not description.strip():
                        st.error("Subject and description are required.")
                    else:
                        ticket = create_ticket(
                            employee["id"],
                            category,
                            subject.strip(),
                            description.strip(),
                            priority
                        )
                        st.success(f"Created {ticket['ticket_number']}")
                        st.rerun()

        tickets = list_tickets(employee["id"])

        if not tickets:
            st.info("No tickets created.")
        else:
            for ticket in tickets:
                with st.container(border=True):
                    st.subheader(
                        f"{ticket['ticket_number']} — {ticket['subject']}"
                    )
                    st.write(ticket["description"])

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Status", ticket["status"])
                    col2.metric("Priority", ticket["priority"])
                    col3.metric(
                        "Assigned to",
                        ticket.get("assigned_to") or "Unassigned"
                    )

                    if ticket.get("resolution"):
                        st.success(f"Resolution: {ticket['resolution']}")

                    with st.expander("Ticket history"):
                        for item in ticket_history(ticket["id"]):
                            st.write(
                                f"**{item['new_status']}** — "
                                f"{item['changed_at']}"
                            )
                            if item.get("comment"):
                                st.caption(item["comment"])

with tabs[4]:
    st.header("Ticket Administration")

    all_tickets = list_tickets()

    if not all_tickets:
        st.info("No tickets available.")
    else:
        selected_ticket = st.selectbox(
            "Select ticket",
            all_tickets,
            format_func=lambda ticket: (
                f"{ticket['ticket_number']} — "
                f"{ticket['employee_name']} — "
                f"{ticket['subject']}"
            )
        )

        with st.form("admin_ticket_form"):
            status = st.selectbox(
                "Status",
                VALID_STATUSES,
                index=VALID_STATUSES.index(selected_ticket["status"])
            )
            assigned_to = st.text_input(
                "Assigned to",
                value=selected_ticket.get("assigned_to") or ""
            )
            comment = st.text_area("Status comment")
            resolution = st.text_area(
                "Resolution",
                value=selected_ticket.get("resolution") or ""
            )

            if st.form_submit_button("Update ticket"):
                update_ticket(
                    selected_ticket["id"],
                    status,
                    assigned_to.strip() or None,
                    resolution.strip() or None,
                    comment.strip()
                )
                st.success("Ticket updated.")
                st.rerun()

with tabs[5]:
    st.header("Policy Library")

    search_term = st.text_input(
        "Search policies",
        placeholder="Example: acceptance criteria, leave, Power BI"
    )

    results = (
        retriever.search(search_term, top_k=10)
        if search_term
        else [{"policy": item, "score": 1.0} for item in retriever.policies]
    )

    st.caption(f"{len(retriever.policies)} separate policy files loaded.")

    for result in results:
        policy = result["policy"]

        with st.expander(f"{policy['id']} — {policy['title']}"):
            st.write(policy["summary"])
            st.markdown("**Policy requirements**")

            for item in policy["details"]:
                st.write(f"- {item}")

            st.markdown("**Employee actions**")

            for item in policy["employee_actions"]:
                st.write(f"- {item}")

            st.markdown(
                f"**Owner:** {policy['owner']}  \\n"
                f"**Category:** {policy['category']}  \\n"
                f"**Status:** {policy['status']}  \\n"
                f"**Escalation:** {policy['escalation']}"
            )
