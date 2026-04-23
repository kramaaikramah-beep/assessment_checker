from pydantic import BaseModel


class ReviewItem(BaseModel):
    question_id: str
    question: str
    answer_status: str
    marker_found: bool
    matched_marker: str | None = None
    matched_text: str | None = None
    answer_word_count: int
    minimum_words: int
    judgement: str
    issue: str
    action: str
    feedback: str
    covered_points: list[str]
    missing_points: list[str]
    answer_sheet_score: float = 0.0
    answer_sheet_covered_points: list[str] = []
    answer_sheet_missing_points: list[str] = []


class ReviewSummary(BaseModel):
    total_questions: int
    answered_questions: int
    blank_questions: int
    missing_questions: int
    markers_found: int
    markers_missing: int
    met: int
    mostly_relevant: int
    partially_met: int
    insufficient_evidence: int
    incorrect_or_off_task: int
    not_yet_assessable: int


class EvaluationResponse(BaseModel):
    review_id: str
    original_filename: str
    reviewed_filename: str
    download_url: str
    unit_id: str | None = None
    unit_name: str | None = None
    unit_file: str
    answer_sheet_filename: str | None = None
    answer_sheet_source: str = "configured_knowledge_base"
    answer_sheet_questions_matched: int = 0
    answer_sheet_questions_missing: int = 0
    answer_sheet_questions_matched_by_order: int = 0
    summary: ReviewSummary
    results: list[ReviewItem]
