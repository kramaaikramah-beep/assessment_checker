import os
from pathlib import Path
from typing import Any

import requests
import streamlit as st


API_BASE_URL = os.getenv("ASSESSMENT_API_URL", "http://127.0.0.1:8000").rstrip("/")
REQUEST_CONNECT_TIMEOUT = int(os.getenv("ASSESSMENT_API_CONNECT_TIMEOUT", "15"))
REQUEST_READ_TIMEOUT = int(os.getenv("ASSESSMENT_API_READ_TIMEOUT", "600"))
ALLOWED_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}
ANSWER_SHEET_ALLOWED_SUFFIXES = {".docx"}
ANSWER_SHEET_SOURCE_LABELS = {
    "configured_knowledge_base": "Configured knowledge base",
    "configured_knowledge_base_fallback": "Uploaded answer sheet could not be mapped. Using configured knowledge base.",
    "mixed_uploaded_and_configured": "Partly matched uploaded answer sheet. Remaining questions use configured knowledge base.",
    "uploaded_answer_sheet": "Uploaded answer sheet",
}


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"] {
            background:
                radial-gradient(circle at top left, rgba(196, 225, 255, 0.85), transparent 28%),
                radial-gradient(circle at top right, rgba(255, 230, 188, 0.7), transparent 24%),
                linear-gradient(180deg, #eef3f8 0%, #f8fafc 44%, #eef4f9 100%);
            color: #18324a;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #11293f 0%, #173854 100%);
        }
        [data-testid="stSidebar"] * {
            color: #f4f8fc;
        }
        .block-container {
            padding-top: 1.1rem;
            padding-bottom: 1.8rem;
            max-width: 1320px;
        }
        [data-testid="stVerticalBlock"] > div:has(> .panel) {
            margin-bottom: 0.95rem;
        }
        [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(19, 53, 87, 0.08);
            border-radius: 18px;
            padding: 0.9rem 1rem;
            box-shadow: 0 18px 30px rgba(21, 38, 56, 0.08);
        }
        [data-testid="column"] {
            padding-top: 0;
        }
        div[data-testid="stFileUploader"] section {
            border-radius: 18px;
            border: 1px dashed rgba(18, 52, 88, 0.2);
            background: rgba(248, 251, 255, 0.95);
            padding: 0.35rem;
        }
        .hero {
            padding: 2rem 2.1rem 1.8rem 2.1rem;
            border-radius: 24px;
            background:
                radial-gradient(circle at top right, rgba(116, 190, 255, 0.18), transparent 30%),
                linear-gradient(135deg, rgba(11, 37, 64, 0.98), rgba(24, 76, 103, 0.96));
            color: #f8fbff;
            border: 1px solid rgba(255, 255, 255, 0.12);
            box-shadow: 0 28px 54px rgba(23, 39, 58, 0.18);
            margin-bottom: 1rem;
        }
        .hero h1 {
            margin: 0 0 0.45rem 0;
            font-size: 2.55rem;
            line-height: 1.05;
        }
        .hero p {
            margin: 0;
            color: rgba(248, 251, 255, 0.88);
            font-size: 1rem;
            max-width: 52rem;
            line-height: 1.55;
        }
        .hero-strip {
            display: flex;
            gap: 0.75rem;
            flex-wrap: wrap;
            margin-top: 1rem;
        }
        .hero-chip {
            padding: 0.45rem 0.8rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.12);
            font-size: 0.84rem;
            font-weight: 600;
        }
        .panel {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(18, 52, 88, 0.08);
            border-radius: 20px;
            padding: 1.15rem 1.2rem;
            box-shadow: 0 18px 32px rgba(31, 48, 66, 0.08);
            margin: 0.2rem 0 0.9rem 0;
        }
        .mini-card {
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid rgba(18, 52, 88, 0.08);
            border-radius: 18px;
            padding: 1rem;
            min-height: 118px;
            margin-bottom: 0.65rem;
            box-shadow: 0 14px 28px rgba(31, 48, 66, 0.05);
        }
        .mini-card h3 {
            margin: 0;
            color: #123458;
            font-size: 0.95rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }
        .mini-card p {
            margin: 0.45rem 0 0 0;
            color: #24384c;
            font-size: 0.95rem;
            line-height: 1.45;
        }
        .status-pill {
            display: inline-block;
            padding: 0.28rem 0.7rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-bottom: 0.95rem;
            color: #123458;
            background: #dceeff;
        }
        .question-card {
            padding: 1rem 1.05rem;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(18, 52, 88, 0.08);
            margin-top: 0.2rem;
        }
        .section-gap {
            height: 0.25rem;
        }
        div[data-testid="stExpander"] {
            margin-bottom: 0.55rem;
        }
        div[data-testid="stDownloadButton"] {
            margin-top: 0.8rem;
        }
        div[data-testid="stFileUploader"] {
            margin-top: 0.35rem;
            margin-bottom: 0.75rem;
        }
        div[data-testid="stButton"] {
            margin-top: 0.15rem;
        }
        .upload-note {
            margin-top: 0.7rem;
            padding: 0.85rem 0.95rem;
            border-radius: 16px;
            background: linear-gradient(135deg, rgba(228, 241, 255, 0.92), rgba(246, 249, 253, 0.96));
            border: 1px solid rgba(18, 52, 88, 0.08);
            color: #1c3954;
        }
        @media (max-width: 900px) {
            .block-container {
                padding-top: 0.8rem;
                padding-bottom: 1.2rem;
            }
            .hero {
                padding: 1.45rem 1.1rem;
            }
            .panel,
            .question-card,
            .mini-card {
                padding-left: 0.95rem;
                padding-right: 0.95rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _call_api(method: str, path: str, **kwargs: Any) -> requests.Response:
    return requests.request(
        method,
        f"{API_BASE_URL}{path}",
        timeout=(REQUEST_CONNECT_TIMEOUT, REQUEST_READ_TIMEOUT),
        **kwargs,
    )


def _backend_online() -> bool:
    try:
        response = _call_api("GET", "/health")
        return response.ok
    except requests.RequestException:
        return False


def _error_message(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text or "The request failed."

    if isinstance(payload, dict):
        return str(payload.get("detail") or payload)
    return str(payload)


def _is_allowed_upload(uploaded_file) -> bool:
    if uploaded_file is None:
        return False
    if uploaded_file.type in ALLOWED_TYPES:
        return True
    return Path(uploaded_file.name).suffix.lower() == ".docx"


def _is_allowed_answer_sheet(uploaded_file) -> bool:
    if uploaded_file is None:
        return False
    return Path(uploaded_file.name).suffix.lower() in ANSWER_SHEET_ALLOWED_SUFFIXES


def _judgement_badge(value: str) -> str:
    tone = {
        "Met": "#d8f1df",
        "Mostly relevant": "#e2ecff",
        "Partially met": "#fff0cf",
        "Insufficient evidence": "#ffe0cc",
        "Incorrect or off task": "#ffd7d9",
        "Not yet assessable": "#f1e3ff",
    }.get(value, "#e9eef5")
    return (
        f"<span style='display:inline-block;padding:0.25rem 0.7rem;border-radius:999px;"
        f"background:{tone};color:#17324d;font-weight:600;font-size:0.82rem;'>{value}</span>"
    )


def _render_overview() -> None:
    st.markdown(
        """
        <section class="hero">
            <div class="status-pill">Trial Version</div>
            <h1>AI Assessment Checker</h1>
            <p>Review assessment submissions with a cleaner workflow, question-level scoring, and a reviewed output file that is ready to share.</p>
            <div class="hero-strip">
                <span class="hero-chip">Professional review dashboard</span>
                <span class="hero-chip">DOCX-first for faster processing</span>
                <span class="hero-chip">Reviewed file download</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
            <div class="mini-card">
                <h3>Submission Intake</h3>
                <p>Student submission and answer sheet both use `.docx` for faster parsing and consistent feedback placement.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div class="mini-card">
                <h3>Systematic Review</h3>
                <p>Maps questions, checks coverage, and inserts concise assessor-style feedback into the reviewed file.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """
            <div class="mini-card">
                <h3>Faster Workflow</h3>
                <p>Using DOCX for both files keeps extraction simpler, comparison faster, and reviewed output more reliable.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_status() -> None:
    with st.sidebar:
        st.subheader("System Status")
        backend_ok = _backend_online()
        if backend_ok:
            st.success("Backend API online")
        else:
            st.error("Backend API not reachable")

        st.caption(f"API URL: `{API_BASE_URL}`")
        st.markdown("Student file: `.docx` only")
        st.markdown("Answer sheet: `.docx` only")
        st.markdown(
            "Recommended structure: `Q1`, `Q2`, `Q3` style questions with each answer directly underneath."
        )


def _submit_file(uploaded_file) -> tuple[dict[str, Any] | None, bytes | None]:
    review_mode = st.session_state.get("review_mode", "Quick assessment")
    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            uploaded_file.type or "application/octet-stream",
        )
    }
    answer_sheet = st.session_state.get("answer_sheet_upload")
    if review_mode == "Compare with answer sheet" and answer_sheet is not None:
        files["answer_sheet"] = (
            answer_sheet.name,
            answer_sheet.getvalue(),
            answer_sheet.type or "application/octet-stream",
        )

    try:
        response = _call_api("POST", "/evaluate", files=files)
    except requests.ReadTimeout:
        st.error(
            "The review took too long to finish. Try a smaller DOCX file "
            "or increase `ASSESSMENT_API_READ_TIMEOUT`."
        )
        return None, None
    except requests.RequestException as exc:
        st.error(f"Could not contact the backend API: {exc}")
        return None, None
    if not response.ok:
        st.error(_error_message(response))
        return None, None

    payload = response.json()
    try:
        download_response = _call_api("GET", payload["download_url"])
    except requests.ReadTimeout:
        st.error("The review finished, but downloading the reviewed file took too long.")
        return payload, None
    except requests.RequestException as exc:
        st.error(f"The review finished, but the reviewed file could not be downloaded: {exc}")
        return payload, None
    if not download_response.ok:
        st.error("The review finished, but the reviewed file could not be downloaded.")
        return payload, None

    return payload, download_response.content


def _normalize_payload(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not payload:
        return payload

    summary = payload.setdefault("summary", {})
    total_questions = summary.get("total_questions", 0)
    summary.setdefault("markers_found", 0)
    summary.setdefault("markers_missing", max(total_questions - summary["markers_found"], 0))

    for item in payload.get("results", []):
        item.setdefault("marker_found", False)
        item.setdefault("matched_marker", None)
        item.setdefault("matched_text", None)

    payload.setdefault("answer_sheet_source", "configured_knowledge_base")
    payload.setdefault("answer_sheet_questions_matched", 0)
    payload.setdefault("answer_sheet_questions_missing", total_questions)
    payload.setdefault("answer_sheet_questions_matched_by_order", 0)

    return payload


def _render_submission() -> None:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Review Submission")
    review_mode = st.radio(
        "Review mode",
        ["Quick assessment", "Compare with answer sheet"],
        horizontal=True,
        help="Use Quick assessment for the faster assessor-style review. Use Compare with answer sheet only when you want direct answer matching.",
        key="review_mode",
    )
    uploaded = st.file_uploader(
        "Upload student assignment",
        type=["docx"],
        help="Upload the student submission as DOCX for faster review and reliable feedback insertion.",
    )
    answer_sheet = None
    if review_mode == "Compare with answer sheet":
        answer_sheet = st.file_uploader(
            "Upload answer sheet",
            type=["docx"],
            help="Upload the assessor answer sheet as DOCX so the app can match answers quickly and consistently.",
            key="answer_sheet_upload",
        )
        st.markdown(
            """
            <div class="upload-note">
                <strong>Answer-sheet rule:</strong> upload the answer sheet in <code>.docx</code> format only.
                This keeps comparison mode faster and consistent with the student DOCX submission flow.
            </div>
            """,
            unsafe_allow_html=True,
        )

    can_submit = uploaded is not None
    if st.button("Run Assessment Review", type="primary", use_container_width=True, disabled=not can_submit):
        if not _is_allowed_upload(uploaded):
            st.error("Unsupported file type. Use a DOCX file.")
        elif review_mode == "Compare with answer sheet" and not answer_sheet:
            st.error("Upload the answer sheet in DOCX format to run comparison mode.")
        elif answer_sheet and not _is_allowed_answer_sheet(answer_sheet):
            st.error("Unsupported answer sheet type. Use a DOCX file.")
        else:
            with st.spinner("Reviewing submission and generating assessor feedback..."):
                payload, reviewed_file = _submit_file(uploaded)
            if payload:
                st.session_state["review_payload"] = payload
                st.session_state["review_file"] = reviewed_file

    if review_mode == "Quick assessment":
        st.caption("Quick assessment is the fastest mode. It checks answer presence, relevance, key points, and minimum answer depth without answer-sheet matching.")
    else:
        st.caption("Comparison mode uses the uploaded DOCX answer sheet to check matching, coverage, and answer quality.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)


def _render_summary(payload: dict[str, Any], reviewed_file: bytes | None) -> None:
    summary = payload["summary"]
    results = payload["results"]
    markers_found = summary.get("markers_found", 0)
    markers_missing = summary.get("markers_missing", summary.get("total_questions", 0) - markers_found)
    improvement_items = (
        summary["partially_met"]
        + summary["insufficient_evidence"]
        + summary["incorrect_or_off_task"]
        + summary["not_yet_assessable"]
    )

    st.subheader("Review Summary")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Questions", summary["total_questions"])
    m2.metric("Answered", summary["answered_questions"])
    m3.metric("Met", summary["met"])
    m4.metric("Needs Attention", improvement_items)
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

    info1, info2 = st.columns([1.2, 1])
    with info1:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(f"**Unit:** {payload.get('unit_name') or payload['unit_file']}")
        st.markdown(f"**Original file:** `{payload['original_filename']}`")
        if payload.get("answer_sheet_filename"):
            st.markdown(f"**Answer sheet:** `{payload['answer_sheet_filename']}`")
        else:
            st.markdown("**Answer sheet:** `Configured knowledge base`")
        st.markdown(
            f"**Answer sheet source:** {ANSWER_SHEET_SOURCE_LABELS.get(payload.get('answer_sheet_source'), payload.get('answer_sheet_source'))}"
        )
        st.markdown(
            f"**Answer sheet mapping:** `{payload.get('answer_sheet_questions_matched', 0)}` matched / `{payload.get('answer_sheet_questions_missing', 0)}` not matched"
        )
        if payload.get("answer_sheet_questions_matched_by_order", 0):
            st.markdown(
                f"**Order fallback used:** `{payload.get('answer_sheet_questions_matched_by_order', 0)}` question(s)"
            )
        st.markdown(f"**Reviewed output:** `{payload['reviewed_filename']}`")
        if reviewed_file:
            st.download_button(
                "Download Reviewed File",
                reviewed_file,
                file_name=payload["reviewed_filename"],
                mime="application/octet-stream",
                use_container_width=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
    with info2:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("**Question Status**")
        st.write(f"Blank answers: `{summary['blank_questions']}`")
        st.write(f"Missing answers: `{summary['missing_questions']}`")
        st.write(f"Signs found in document: `{markers_found}`")
        st.write(f"Signs not found: `{markers_missing}`")
        st.write(f"Mostly relevant: `{summary['mostly_relevant']}`")
        st.write(f"Partially met: `{summary['partially_met']}`")
        st.write(f"Insufficient evidence: `{summary['insufficient_evidence']}`")
        st.write(f"Incorrect/off task: `{summary['incorrect_or_off_task']}`")
        st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("Question-by-Question Review")
    table_rows = [
        {
            "Question": item["question_id"],
            "Sign Found": "Yes" if item.get("marker_found") else "No",
            "Judgement": item["judgement"],
            "Answer Status": item["answer_status"],
            "Words": item["answer_word_count"],
            "Target": item["minimum_words"],
            "Answer-Sheet Match": f"{int((item.get('answer_sheet_score') or 0) * 100)}%",
        }
        for item in results
    ]
    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    for item in results:
        with st.expander(f"{item['question_id']} - {item['judgement']}"):
            st.markdown('<div class="question-card">', unsafe_allow_html=True)
            st.markdown(_judgement_badge(item["judgement"]), unsafe_allow_html=True)
            st.markdown(f"**Question:** {item['question']}")
            st.markdown(
                f"**Answer status:** `{item['answer_status']}` | **Words:** `{item['answer_word_count']}` / `{item['minimum_words']}`"
            )
            st.markdown(
                f"**Answer-sheet match:** `{int((item.get('answer_sheet_score') or 0) * 100)}%`"
            )
            st.markdown(
                f"**Configured sign found:** `{'Yes' if item.get('marker_found') else 'No'}`"
            )
            if item.get("matched_marker"):
                st.markdown(f"**Matched sign:** `{item['matched_marker']}`")
            if item.get("matched_text"):
                st.markdown(f"**Matched document text:** {item['matched_text']}")
            st.markdown(f"**Issue:** {item['issue']}")
            st.markdown(f"**Action required:** {item['action']}")
            if item["covered_points"]:
                st.markdown("**Covered points:** " + ", ".join(item["covered_points"]))
            if item["missing_points"]:
                st.markdown("**Missing points:** " + ", ".join(item["missing_points"]))
            if item.get("answer_sheet_covered_points"):
                st.markdown("**Matched answer-sheet ideas:** " + ", ".join(item["answer_sheet_covered_points"]))
            if item.get("answer_sheet_missing_points"):
                st.markdown("**Missing answer-sheet ideas:** " + ", ".join(item["answer_sheet_missing_points"]))
            st.markdown(f"**Feedback inserted into file:** {item['feedback']}")
            st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(
        page_title="AI Assessment Checker",
        page_icon="A",
        layout="wide",
    )
    _inject_styles()
    _render_status()
    _render_overview()
    _render_submission()

    payload = st.session_state.get("review_payload")
    payload = _normalize_payload(payload)
    if payload:
        st.session_state["review_payload"] = payload
    reviewed_file = st.session_state.get("review_file")
    if payload:
        _render_summary(payload, reviewed_file)


if __name__ == "__main__":
    main()
