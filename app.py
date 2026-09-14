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
    "Коммуникативная задача"
)

communication_goal = st.text_area(
    "Что должен сообщать этот визуал?",
    placeholder=(
        "Например: привлечь внимание к мероприятию, "
        "сообщить дату и место проведения, "
        "мотивировать зрителя зарегистрироваться."
    ),
    height=100
)


target_action = st.text_input(
    "Какое действие должен совершить зритель?",
    placeholder=(
        "Например: зарегистрироваться, "
        "купить товар, перейти по ссылке."
    )
)


# ============================================================
# IMAGE UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    "Загрузите графический материал",
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
        "🔍 Провести визуальный аудит",
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

    st.divider()

    st.header(
        "Итоговая оценка"
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
        "Анализ по 15 критериям"
    )

    st.caption(
        "Каждая оценка сопровождается наблюдением, "
        "визуальными доказательствами и объяснением "
        "влияния на восприятие."
    )


    principles = [

        # Композиционная организация
        (
            "Композиция",
            result.composition
        ),

        (
            "Баланс",
            result.balance
        ),

        (
            "Пропорции и масштаб",
            result.proportion_scale
        ),

        # Иерархия и внимание
        (
            "Визуальная иерархия",
            result.visual_hierarchy
        ),

        (
            "Фокусная точка",
            result.focal_point
        ),

        (
            "Контраст",
            result.contrast
        ),

        # Пространственная организация
        (
            "Негативное пространство",
            result.negative_space
        ),

        (
            "Выравнивание",
            result.alignment
        ),

        (
            "Близость и группировка",
            result.proximity_grouping
        ),

        # Визуальные средства
        (
            "Типографика",
            result.typography
        ),

        (
            "Цвет",
            result.color
        ),

        (
            "Читаемость и доступность",
            result.readability_accessibility
        ),

        # Целостность и коммуникация
        (
            "Повтор и ритм",
            result.repetition_rhythm
        ),

        (
            "Единство и визуальная согласованность",
            result.unity_coherence
        ),

        (
            "Коммуникативная эффективность",
            result.communication_effectiveness
        ),
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
            )


            st.write(
                "### Влияние на восприятие"
            )

            st.write(
                principle.perceptual_effect
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
            )


            if principle.recommendation:

                st.write(
                    "### Что изменить"
                )

                st.write(
                    principle.recommendation
                )


            st.caption(
                f"Статус критерия: {principle.status}"
            )


    # ========================================================
    # PRIORITY ISSUES
    # ========================================================

    st.divider()

    st.header(
        "Приоритетные проблемы"
    )

    for issue in result.priority_issues:

        with st.container(
            border=True
        ):

            st.subheader(
                f"{issue.priority.upper()} — "
                f"{issue.principle}"
            )

            st.write(
                f"**Проблема:** {issue.issue}"
            )

            st.write(
                f"**Доказательство:** "
                f"{issue.evidence}"
            )

            st.write(
                f"**Влияние на восприятие:** "
                f"{issue.perceptual_impact}"
            )

            st.write(
                f"**Что сделать:** "
                f"{issue.action}"
            )


    # ========================================================
    # STRENGTHS
    # ========================================================

    st.divider()

    st.header(
        "Сильные стороны"
    )

    for strength in result.strengths:

        st.markdown(
            f"✓ {strength}"
        )


    # ========================================================
    # TOP PROBLEMS
    # ========================================================

    st.header(
        "3 главные проблемы"
    )

    for problem in result.most_important_problems:

        st.markdown(
            f"• {problem}"
        )


    # ========================================================
    # RECOMMENDATIONS
    # ========================================================

    st.header(
        "3 конкретных рекомендации"
    )

    for recommendation in result.concrete_recommendations:

        st.markdown(
            f"→ {recommendation}"
        )


    # ========================================================
    # IMPROVEMENT PROMPT
    # ========================================================

    st.divider()

    st.header(
        "Промпт для профессионального редизайна"
    )

    st.caption(
        "Промпт сформирован на основе выявленных "
        "проблем. Он предназначен не для косметического "
        "улучшения, а для устранения причин визуальной "
        "неэффективности."
    )

    st.code(
        result.improvement_prompt,
        language="text"
    )


    # ========================================================
    # DESIGNER BRIEF
    # ========================================================

    st.header(
        "Задание дизайнеру"
    )

    st.code(
        result.designer_brief,
        language="text"
    )
