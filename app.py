import streamlit as st

from audit import analyze_image
from utils import (
    prepare_image,
    get_image_dimensions
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="V-AUDIT",
    page_icon="🎨",
    layout="wide"
)


# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
    <style>

    .main {
        background-color: #f7f4f1;
    }

    .block-container {
        max-width: 1200px;
        padding-top: 3rem;
        padding-bottom: 5rem;
    }

    h1 {
        font-size: 42px;
        font-weight: 700;
        letter-spacing: -1px;
    }

    .subtitle {
        font-size: 18px;
        color: #666;
        margin-bottom: 30px;
    }

    .info-box {
        background: #ffffff;
        padding: 18px 22px;
        border-radius: 12px;
        margin-bottom: 25px;
        border: 1px solid #e5e0dc;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.title(
    "V-AUDIT"
)

st.markdown(
    """
    <div class="subtitle">
    ИИ-аудит и интеллектуальный редизайн графических материалов
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="info-box">

    <b>Как работает V-AUDIT</b><br><br>

    Система анализирует графический материал
    по 15 формализованным критериям дизайна,
    фиксирует визуальные доказательства,
    определяет наиболее значимые проблемы
    и формирует конкретные рекомендации
    для последующего редизайна.

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# COMMUNICATION CONTEXT
# ============================================================

st.subheader(
    "Communication Context"
)

communication_goal = st.text_area(
    "What should this visual communicate?",
    placeholder=(
        "Например: привлечь внимание к мероприятию, "
        "сообщить дату и место проведения, "
        "мотивировать зрителя зарегистрироваться."
    ),
    height=100
)

target_action = st.text_input(
    "What should the viewer do?",
    placeholder=(
        "Например: зарегистрироваться, "
        "купить товар, перейти по ссылке."
    )
)


# ============================================================
# IMAGE UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    "Upload graphic material",
    type=[
        "jpg",
        "jpeg",
        "png",
        "webp"
    ]
)


# ============================================================
# ANALYSIS
# ============================================================

if uploaded_file:

    st.image(
        uploaded_file,
        caption="Изображение для анализа",
        use_container_width=True
    )

    width, height = get_image_dimensions(
        uploaded_file
    )

    st.caption(
        f"Размер изображения: {width} × {height} px"
    )

    if st.button(
        "🔍 Run Visual Audit",
        type="primary"
    ):

        with st.spinner(
            "AI анализирует визуальную структуру..."
        ):

            try:

                image_bytes = prepare_image(
                    uploaded_file
                )

                result = analyze_image(
                    image_bytes,
                    communication_goal,
                    target_action
                )

                st.session_state[
                    "audit_result"
                ] = result

            except Exception as error:

                st.error(
                    f"Ошибка анализа: {error}"
                )


# ============================================================
# RESULTS
# ============================================================

if "audit_result" in st.session_state:

    result = st.session_state[
        "audit_result"
    ]

    # ========================================================
    # SCORES
    # ========================================================

    st.divider()

    st.header(
        "Overall Assessment"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Design Score",
            f"{result.overall_design_score}/100"
        )

    with col2:

        st.metric(
            "Communication Score",
            f"{result.communication_score}/100"
        )


    # ========================================================
    # PRINCIPLES
    # ========================================================

    st.divider()

    st.header(
        "Analysis by 15 Principles"
    )

    st.caption(
        "Каждая оценка сопровождается наблюдением, "
        "визуальными доказательствами, объяснением "
        "значения и влияния на восприятие."
    )


    principles = [

        (
            "Composition",
            result.composition
        ),

        (
            "Visual Hierarchy",
            result.visual_hierarchy
        ),

        (
            "Balance",
            result.balance
        ),

        (
            "Contrast",
            result.contrast
        ),

        (
            "Typography",
            result.typography
        ),

        (
            "Color",
            result.color
        ),

        (
            "Negative Space",
            result.negative_space
        ),

        (
            "Alignment",
            result.alignment
        ),

        (
            "Proximity & Grouping",
            result.proximity_grouping
        ),

        (
            "Repetition & Rhythm",
            result.repetition_rhythm
        ),

        (
            "Unity & Coherence",
            result.unity_coherence
        ),

        (
            "Readability & Accessibility",
            result.readability_accessibility
        ),

        (
            "Focal Point",
            result.focal_point
        ),

        (
            "Proportion & Scale",
            result.proportion_scale
        ),

        (
            "Communication Effectiveness",
            result.communication_effectiveness
        )
    ]


    for name, principle in principles:

        with st.expander(
            f"{name} — {principle.score}/100"
        ):

            st.write(
                "### Что видно"
            )

            st.write(
                principle.observation
                or "Недостаточно данных."
            )


            st.write(
                "### Визуальные доказательства"
            )

            if principle.evidence:

                for evidence in principle.evidence:

                    st.markdown(
                        f"- {evidence}"
                    )

            else:

                st.write(
                    "Доказательства не указаны."
                )


            st.write(
                "### Почему это важно"
            )

            st.write(
                principle.rationale
                or "Обоснование не указано."
            )


            st.write(
                "### Влияние на восприятие"
            )

            st.write(
                principle.perceptual_effect
                or "Влияние не указано."
            )


            if principle.problem:

                st.write(
                    "### Проблема"
                )

                st.write(
                    principle.problem
                )


            st.write(
                "### Почему такая оценка"
            )

            st.write(
                principle.score_justification
                or "Обоснование оценки не указано."
            )


            if principle.recommendation:

                st.write(
                    "### Что изменить"
                )

                st.write(
                    principle.recommendation
                )


# ============================================================
# PRIORITY ISSUES
# ============================================================

    st.divider()

    st.header(
        "Priority Issues"
    )

    if result.priority_issues:

        for issue in result.priority_issues:

            priority = (
                issue.priority
                or "medium"
            ).upper()

            with st.container(
                border=True
            ):

                st.subheader(
                    f"{priority} — "
                    f"{issue.principle}"
                )

                if issue.issue:

                    st.write(
                        f"**Проблема:** "
                        f"{issue.issue}"
                    )

                if issue.evidence:

                    st.write(
                        f"**Доказательство:** "
                        f"{issue.evidence}"
                    )

                if issue.perceptual_impact:

                    st.write(
                        f"**Влияние на восприятие:** "
                        f"{issue.perceptual_impact}"
                    )

                if issue.action:

                    st.write(
                        f"**Что сделать:** "
                        f"{issue.action}"
                    )

    else:

        st.success(
            "Существенных приоритетных проблем не обнаружено."
        )


# ============================================================
# STRENGTHS
# ============================================================

    st.divider()

    st.header(
        "Strengths"
    )

    if result.strengths:

        for strength in result.strengths:

            st.markdown(
                f"✓ {strength}"
            )

    else:

        st.write(
            "Сильные стороны не были выделены."
        )


# ============================================================
# TOP PROBLEMS
# ============================================================

    st.header(
        "3 Main Problems"
    )

    if result.most_important_problems:

        for problem in result.most_important_problems:

            st.markdown(
                f"• {problem}"
            )

    else:

        st.write(
            "Существенные проблемы не определены."
        )


# ============================================================
# RECOMMENDATIONS
# ============================================================

    st.header(
        "3 Concrete Recommendations"
    )

    if result.concrete_recommendations:

        for recommendation in result.concrete_recommendations:

            st.markdown(
                f"→ {recommendation}"
            )

    else:

        st.write(
            "Рекомендации не сформированы."
        )


# ============================================================
# IMPROVEMENT PROMPT
# ============================================================

    st.divider()

    st.header(
        "Professional Redesign Prompt"
    )

    st.caption(
        "Промпт формируется на основе выявленных "
        "проблем и предназначен для содержательного "
        "редизайна, а не косметического улучшения."
    )

    if result.improvement_prompt:

        st.code(
            result.improvement_prompt,
            language="text"
        )

    else:

        st.warning(
            "Промпт для редизайна не сформирован."
        )


# ============================================================
# DESIGNER BRIEF
# ============================================================

    st.header(
        "Designer Brief"
    )

    if result.designer_brief:

        st.code(
            result.designer_brief,
            language="text"
        )

    else:

        st.warning(
            "Designer Brief не сформирован."
        )
