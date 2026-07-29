from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
POLICY_DIR = BASE_DIR / "policies"
PLAN_FILE = BASE_DIR / "data" / "onboarding_plan.json"
DATABASE_FILE = BASE_DIR / "onboarding.db"

GEMINI_MODEL = "gemini-2.0-flash"
TOP_K = 5
MIN_SIMILARITY = 0.04
