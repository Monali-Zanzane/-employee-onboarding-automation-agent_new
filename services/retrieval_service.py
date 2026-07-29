import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class PolicyRetriever:
    def __init__(self, policy_dir, min_similarity=0.04):
        self.policy_dir = Path(policy_dir)
        self.min_similarity = min_similarity
        self.policies = []
        self.documents = []

        for path in self.policy_dir.rglob("*.json"):
            if path.name == "policy_index.json":
                continue
            policy = json.loads(path.read_text(encoding="utf-8"))
            self.policies.append(policy)
            self.documents.append(" ".join([
                policy.get("title",""),
                policy.get("category",""),
                policy.get("topic",""),
                policy.get("summary",""),
                " ".join(policy.get("details",[])),
                " ".join(policy.get("employee_actions",[])),
                " ".join(policy.get("keywords",[])),
            ]))

        if not self.policies:
            raise ValueError("No policy files found.")

        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1,2))
        self.matrix = self.vectorizer.fit_transform(self.documents)

    def search(self, query, top_k=5):
        vector = self.vectorizer.transform([query])
        scores = cosine_similarity(vector, self.matrix)[0]
        ranked = scores.argsort()[::-1]
        results = []
        for index in ranked[:top_k]:
            score = float(scores[index])
            if score >= self.min_similarity:
                results.append({"policy": self.policies[index], "score": score})
        return results
