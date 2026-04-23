import json
from pathlib import Path


def detect_unit(text, knowledge_dir="knowledge"):
    knowledge_dir = Path(knowledge_dir)
    with open(knowledge_dir / "metadata.json", encoding="utf-8") as f:
        metadata = json.load(f)

    best_match = None
    best_score = 0
    lowered_text = text.lower()

    for unit in metadata["units"]:
        score = 0
        for keyword in unit["keywords"]:
            if keyword.lower() in lowered_text:
                score += 1
        if score > best_score:
            best_score = score
            best_match = unit["file"]

    return best_match or metadata["units"][0]["file"]
