def fallback_answer(results):
    if not results:
        return (
            "I could not find a sufficiently relevant policy. "
            "Please rephrase your question or create a support ticket."
        )

    policy = results[0]["policy"]
    details = "\n".join(f"- {item}" for item in policy.get("details",[])[:4])
    actions = "\n".join(f"- {item}" for item in policy.get("employee_actions",[])[:4])

    return (
        f"### {policy['title']}\n"
        f"{policy.get('summary','')}\n\n"
        f"**What the policy requires**\n{details}\n\n"
        f"**Your actions**\n{actions}\n\n"
        f"**Escalation:** {policy.get('escalation','Not specified')}"
    )

def generate_answer(question, results, api_key, model_name, employee, score):
    if not api_key:
        return fallback_answer(results), "Gemini is disabled; showing a grounded retrieval response."

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)

        context = "\n\n".join(
            f"{result['policy']['id']} - {result['policy']['title']}\n"
            + "\n".join(result["policy"].get("details",[]))
            for result in results
        )

        prompt = (
            "You are Aida, an employee onboarding assistant. "
            "Answer only from the supplied policy context. "
            "Be practical and mention source policy IDs.\n\n"
            f"Employee: {employee['name']}\n"
            f"Role: {employee['role']}\n"
            f"Onboarding day: {employee['onboarding_day']}\n"
            f"Onboarding score: {score}%\n"
            f"Question: {question}\n\n"
            f"Policy context:\n{context}"
        )

        response = model.generate_content(prompt)
        text = getattr(response, "text", "") or ""
        return text.strip() or fallback_answer(results), None

    except Exception:
        return fallback_answer(results), "Gemini was unavailable; showing a grounded retrieval response."
