import re
from services.database_service import get_connection

POSITIVE = {"good","great","happy","helpful","clear","excellent","easy","thank","resolved","excited"}
NEGATIVE = {"bad","confused","blocked","unable","frustrated","difficult","angry","stuck","problem","issue","worried","overwhelmed"}
URGENT = {"harassment","discrimination","retaliation","unsafe","threat","data leak","security breach","stolen","violence"}

def analyze_sentiment(message):
    words = re.findall(r"[a-zA-Z']+", message.lower())
    pos = sum(word in POSITIVE for word in words)
    neg = sum(word in NEGATIVE for word in words)
    urgent_terms = sorted({term for term in URGENT if term in message.lower()})
    raw = pos - neg
    if urgent_terms or raw < 0:
        label = "Negative"
    elif raw > 0:
        label = "Positive"
    else:
        label = "Neutral"
    score = max(-1.0, min(1.0, raw / max(1, len(words)/5)))
    needs_support = bool(urgent_terms) or neg >= 1
    return {
        "label": label,
        "score": round(score,2),
        "needs_support": needs_support,
        "urgent_terms": urgent_terms,
        "recommendation": (
            "Offer targeted help and consider creating a support ticket."
            if needs_support else
            "Continue normal onboarding support."
        ),
    }

def save_feedback(employee_id, message, result):
    with get_connection() as connection:
        connection.execute(
            '''
            INSERT INTO feedback(
                employee_id,message,sentiment_label,sentiment_score,
                needs_support,urgent_terms
            ) VALUES(?,?,?,?,?,?)
            ''',
            (
                employee_id,message,result["label"],result["score"],
                1 if result["needs_support"] else 0,
                ",".join(result["urgent_terms"])
            )
        )
