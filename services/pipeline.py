from pathlib import Path
import json
from collections import Counter

from core.annotator.word_comment_writer import annotate_docx
from core.evaluator.evaluator import evaluate_answer
from core.extractor.answer_mapper import map_answers
from core.parser.docx_parser import parse_docx
from core.parser.structure_detector import discover_questions
from core.router.unit_router import detect_unit


ROOT_DIR = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = ROOT_DIR / "knowledge"


def _parse_submission(path: Path):
    suffix = path.suffix.lower()
    if suffix != ".docx":
        raise ValueError("The trial build supports .docx assessment files only.")
    return parse_docx(path)


def _load_unit(paragraphs):
    full_text = " ".join(block.text for block in paragraphs)
    unit_file = detect_unit(full_text, KNOWLEDGE_DIR)

    with open(KNOWLEDGE_DIR / unit_file, encoding="utf-8") as f:
        unit = json.load(f)

    marker_config = unit.get("question_markers", {})
    configured_questions = unit.get("questions", [])
    discovered_questions = discover_questions(paragraphs, configured_questions, marker_config)
    effective_questions = []
    configured_by_id = {question["id"]: question for question in configured_questions}

    for discovered in discovered_questions:
        configured = configured_by_id.get(discovered["id"], {})
        effective_questions.append(
            {
                "id": discovered["id"],
                "question": configured.get("question") or discovered["question"],
                "markers": list(
                    dict.fromkeys((configured.get("markers", []) + discovered.get("markers", [])))
                ),
                "minimum_words": configured.get("minimum_words", 35),
                "key_points": configured.get("key_points", []),
                "answer_sheet": configured.get("answer_sheet", ""),
                "source_text": discovered.get("source_text", discovered["question"]),
            }
        )

    if not effective_questions:
        effective_questions = configured_questions

    return unit, unit_file, marker_config, effective_questions


def _map_answers_by_order(blocks, effective_questions):
    discovered_questions = discover_questions(blocks, [], {"match_question_text": False})
    if not discovered_questions:
        return {}

    generic_answers = map_answers(blocks, discovered_questions, {"match_question_text": False})
    ordered_answers = []
    for question in discovered_questions:
        answer = generic_answers.get(question["id"], {}).get("answer", "").strip()
        if answer:
            ordered_answers.append(answer)

    if not ordered_answers:
        return {}

    fallback = {}
    for index, question in enumerate(effective_questions):
        if index >= len(ordered_answers):
            break
        fallback[question["id"]] = ordered_answers[index]
    return fallback


def _merge_uploaded_answer_sheet(answer_sheet_path, effective_questions, marker_config):
    if not answer_sheet_path:
        return effective_questions, {
            "filename": None,
            "source": "configured_knowledge_base",
            "matched_questions": 0,
            "missing_questions": len(effective_questions),
        }

    answer_sheet_blocks = _parse_submission(Path(answer_sheet_path))
    mapped_answers = map_answers(answer_sheet_blocks, effective_questions, marker_config)
    ordered_fallback_answers = _map_answers_by_order(answer_sheet_blocks, effective_questions)
    merged_questions = []
    matched_count = 0
    matched_by_order = 0

    for question in effective_questions:
        sheet_answer = mapped_answers.get(question["id"], {}).get("answer", "").strip()
        if not sheet_answer:
            sheet_answer = ordered_fallback_answers.get(question["id"], "").strip()
        merged_question = dict(question)
        if sheet_answer:
            merged_question["answer_sheet"] = sheet_answer
            matched_count += 1
            if not mapped_answers.get(question["id"], {}).get("answer", "").strip():
                matched_by_order += 1
        merged_questions.append(merged_question)

    total_questions = len(effective_questions)
    if matched_count == 0:
        source = "configured_knowledge_base_fallback"
    elif matched_count < total_questions:
        source = "mixed_uploaded_and_configured"
    else:
        source = "uploaded_answer_sheet"

    return merged_questions, {
        "filename": Path(answer_sheet_path).name,
        "source": source,
        "matched_questions": matched_count,
        "missing_questions": max(total_questions - matched_count, 0),
        "matched_by_order": matched_by_order,
    }


def run_pipeline(input_path, output_path, answer_sheet_path=None):
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    paragraphs = _parse_submission(input_path)
    unit, unit_file, marker_config, effective_questions = _load_unit(paragraphs)
    effective_questions, answer_sheet_info = _merge_uploaded_answer_sheet(
        answer_sheet_path,
        effective_questions,
        marker_config,
    )

    answers = map_answers(paragraphs, effective_questions, marker_config)

    evaluation_results = {}
    review_items = []

    for q in effective_questions:
        mapped = answers.get(q["id"], {})
        answer = mapped.get("answer", "")
        feedback = evaluate_answer(q, answer)
        judgement = feedback["judgement"]
        word_count = len(answer.split()) if answer else 0
        evaluation_results[q["id"]] = {
            "feedback": feedback["feedback"],
            "anchor_index": mapped.get("end_index") or mapped.get("start_index"),
        }
        review_items.append(
            {
                "question_id": q["id"],
                "question": q.get("question", ""),
                "detected_question_text": q.get("source_text", q.get("question", "")),
                "answer_status": mapped.get("status", "missing"),
                "marker_found": mapped.get("marker_found", False),
                "matched_marker": mapped.get("matched_marker"),
                "matched_text": mapped.get("matched_text"),
                "answer_word_count": word_count,
                "minimum_words": q.get("minimum_words", 0),
                "judgement": judgement,
                "issue": feedback["issue"],
                "action": feedback["action"],
                "feedback": feedback["feedback"],
                "covered_points": feedback["covered_points"],
                "missing_points": feedback["missing_points"],
                "answer_sheet_score": feedback.get("answer_sheet_score", 0.0),
                "answer_sheet_covered_points": feedback.get("answer_sheet_covered_points", []),
                "answer_sheet_missing_points": feedback.get("answer_sheet_missing_points", []),
            }
        )

    judgement_counts = Counter(item["judgement"] for item in review_items)
    answer_status_counts = Counter(item["answer_status"] for item in review_items)
    marker_counts = Counter(bool(item["marker_found"]) for item in review_items)

    annotate_docx(input_path, output_path, evaluation_results)

    return {
        "output_path": str(output_path),
        "unit_id": unit.get("unit_id"),
        "unit_name": unit.get("unit_name"),
        "unit_file": unit_file,
        "answer_sheet_filename": answer_sheet_info["filename"],
        "answer_sheet_source": answer_sheet_info["source"],
        "answer_sheet_questions_matched": answer_sheet_info["matched_questions"],
        "answer_sheet_questions_missing": answer_sheet_info["missing_questions"],
        "answer_sheet_questions_matched_by_order": answer_sheet_info.get("matched_by_order", 0),
        "summary": {
            "total_questions": len(review_items),
            "answered_questions": answer_status_counts.get("answered", 0),
            "blank_questions": answer_status_counts.get("blank", 0),
            "missing_questions": answer_status_counts.get("missing", 0),
            "markers_found": marker_counts.get(True, 0),
            "markers_missing": marker_counts.get(False, 0),
            "met": judgement_counts.get("Met", 0),
            "mostly_relevant": judgement_counts.get("Mostly relevant", 0),
            "partially_met": judgement_counts.get("Partially met", 0),
            "insufficient_evidence": judgement_counts.get("Insufficient evidence", 0),
            "incorrect_or_off_task": judgement_counts.get("Incorrect or off task", 0),
            "not_yet_assessable": judgement_counts.get("Not yet assessable", 0),
        },
        "results": review_items,
    }
