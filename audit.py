import json
import re

import streamlit as st
from google import genai
from google.genai import types

from prompts import SYSTEM_PROMPT
from schemas import AuditResult, PriorityIssue


MODEL = "gemini-2.5-flash"


# ============================================================
# ПОДКЛЮЧЕНИЕ GEMINI
# ============================================================

def get_client():

    return genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )


# ============================================================
# ОСНОВНОЙ АНАЛИЗ
# ============================================================

def analyze_image(
    image_bytes: bytes,
    communication_goal: str = "",
    target_action: str = ""
):

    client = get_client()

    image_part = types.Part.from_bytes(
        data=image_bytes,
        mime_type="image/jpeg"
    )

    user_prompt = build_user_prompt(
        communication_goal,
        target_action
    )

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            image_part,
            user_prompt
        ],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.2,
        )
    )

    if not response.text:

        raise ValueError(
            "Gemini не вернул результат."
        )

    result = parse_result(
        response.text
    )

    result.overall_design_score = (
        calculate_design_score(result)
    )

    result.communication_score = (
        normalize_score(
            result.communication_effectiveness.score
        )
    )

    result.priority_issues = (
        build_priority_issues(result)
    )

    return result


# ============================================================
# PROMPT ПОЛЬЗОВАТЕЛЯ
# ============================================================

def build_user_prompt(
    communication_goal: str = "",
    target_action: str = ""
):

    goal = (
        communication_goal.strip()
        if communication_goal
        else "Не предоставлена."
    )

    action = (
        target_action.strip()
        if target_action
        else "Не предоставлено."
    )

    return f"""
Проведи профессиональный визуальный аудит
предоставленного графического материала.

КОММУНИКАТИВНАЯ ЗАДАЧА:
{goal}

ПРЕДПОЛАГАЕМОЕ ДЕЙСТВИЕ ЗРИТЕЛЯ:
{action}

Если коммуникативная задача или действие
не предоставлены, НЕ придумывай их.

Проанализируй изображение по всем 15 критериям.

Для каждого критерия верни:

score
status
observation
evidence
rationale
perceptual_effect
problem
recommendation
score_justification

ВАЖНО:

evidence может быть строкой или списком.
Каждое доказательство должно описывать
реально наблюдаемый элемент изображения.

НЕ придумывай элементы, которых нет
на изображении.

Если существенной проблемы по критерию нет,
поле problem должно быть null,
а recommendation должно быть null.

Не называй критерий проблемным только
для того, чтобы заполнить поле.

Оценка должна соответствовать фактическому
качеству изображения.

Высокая оценка означает эффективную реализацию
принципа.

Низкая оценка означает наличие конкретной
визуальной проблемы.

Верни:

- strengths;
- most_important_problems;
- concrete_recommendations;
- improvement_prompt;
- designer_brief.

priority_issues НЕ формируй.

Эти проблемы будут рассчитаны программой
на основании оценок и описаний.

Не возвращай:

overall_design_score
communication_score

Эти показатели рассчитываются программой.

Не добавляй комментариев вне JSON.

Верни только JSON.
"""


# ============================================================
# РАЗБОР РЕЗУЛЬТАТА GEMINI
# ============================================================

def parse_result(
    raw_text: str
):

    cleaned = clean_json_text(
        raw_text
    )

    try:

        data = json.loads(
            cleaned
        )

    except json.JSONDecodeError as error:

        raise ValueError(
            "Gemini вернул некорректный JSON: "
            f"{error}"
        )

    data = normalize_result_data(
        data
    )

    try:

        result = AuditResult.model_validate(
            data
        )

    except Exception as error:

        raise ValueError(
            "Не удалось обработать результат Gemini.\n"
            f"{error}"
        )

    return result


# ============================================================
# НОРМАЛИЗАЦИЯ
# ============================================================

def normalize_result_data(
    data: dict
):

    principle_names = [

        "composition",
        "visual_hierarchy",
        "balance",
        "contrast",
        "typography",
        "color",
        "negative_space",
        "alignment",
        "proximity_grouping",
        "repetition_rhythm",
        "unity_coherence",
        "readability_accessibility",
        "focal_point",
        "proportion_scale",
        "communication_effectiveness",

    ]


    for name in principle_names:

        principle = data.get(
            name
        )

        if not isinstance(
            principle,
            dict
        ):
            continue


        # SCORE

        principle["score"] = normalize_score(
            principle.get(
                "score",
                50
            )
        )


        # STATUS

        status = principle.get(
            "status",
            "applicable"
        )

        if status not in [
            "applicable",
            "limited",
            "not_applicable"
        ]:

            status = "applicable"

        principle["status"] = status


        # EVIDENCE

        evidence = principle.get(
            "evidence"
        )

        if evidence is None:

            principle["evidence"] = []

        elif isinstance(
            evidence,
            str
        ):

            principle["evidence"] = [
                evidence
            ]

        elif isinstance(
            evidence,
            list
        ):

            principle["evidence"] = [
                str(item)
                for item in evidence
                if item is not None
            ]

        else:

            principle["evidence"] = [
                str(evidence)
            ]


        # TEXT FIELDS

        for field in [

            "observation",
            "rationale",
            "perceptual_effect",
            "score_justification",

        ]:

            principle[field] = convert_to_text(
                principle.get(
                    field,
                    ""
                )
            )


        # OPTIONAL FIELDS

        for field in [

            "problem",
            "recommendation",

        ]:

            value = principle.get(
                field
            )

            if value is None:

                principle[field] = None

            else:

                converted = convert_to_text(
                    value
                )

                principle[field] = (
                    converted
                    if converted.strip()
                    else None
                )


    # LISTS

    data["strengths"] = normalize_string_list(
        data.get(
            "strengths",
            []
        )
    )


    data["most_important_problems"] = (
        normalize_string_list(
            data.get(
                "most_important_problems",
                []
            )
        )
    )


    data["concrete_recommendations"] = (
        normalize_string_list(
            data.get(
                "concrete_recommendations",
                []
            )
        )
    )


    # PROMPT

    data["improvement_prompt"] = (
        convert_to_text(
            data.get(
                "improvement_prompt",
                ""
            )
        )
    )


    # DESIGNER BRIEF

    data["designer_brief"] = (
        convert_to_text(
            data.get(
                "designer_brief",
                ""
            )
        )
    )


    # Gemini priority_issues игнорируем.

    data["priority_issues"] = []


    return data


# ============================================================
# ПРЕОБРАЗОВАНИЕ В ТЕКСТ
# ============================================================

def convert_to_text(
    value
) -> str:

    if value is None:

        return ""


    if isinstance(
        value,
        str
    ):

        return value


    if isinstance(
        value,
        list
    ):

        return "\n".join(
            str(item)
            for item in value
        )


    if isinstance(
        value,
        dict
    ):

        parts = []

        for key, item in value.items():

            readable_key = (
                str(key)
                .replace(
                    "_",
                    " "
                )
                .capitalize()
            )

            if isinstance(
                item,
                list
            ):

                item_text = ", ".join(
                    str(x)
                    for x in item
                )

            elif isinstance(
                item,
                dict
            ):

                item_text = json.dumps(
                    item,
                    ensure_ascii=False
                )

            else:

                item_text = str(item)

            parts.append(
                f"{readable_key}: {item_text}"
            )

        return "\n".join(
            parts
        )


    return str(value)


# ============================================================
# СПИСОК СТРОК
# ============================================================

def normalize_string_list(
    value
):

    if value is None:

        return []


    if isinstance(
        value,
        list
    ):

        result = []

        for item in value:

            text = convert_to_text(
                item
            )

            if text.strip():

                result.append(
                    text
                )

        return result


    if isinstance(
        value,
        str
    ):

        if value.strip():

            return [
                value.strip()
            ]

        return []


    return [
        convert_to_text(value)
    ]


# ============================================================
# ОЧИСТКА JSON
# ============================================================

def clean_json_text(
    text: str
) -> str:

    text = text.strip()


    if text.startswith(
        "```"
    ):

        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text
        )

        text = re.sub(
            r"\s*```$",
            "",
            text
        )


    return text.strip()


# ============================================================
# НОРМАЛИЗАЦИЯ ОЦЕНКИ
# ============================================================

def normalize_score(
    value
) -> int:

    if isinstance(
        value,
        (int, float)
    ):

        return max(
            0,
            min(
                100,
                int(value)
            )
        )


    if isinstance(
        value,
        str
    ):

        match = re.search(
            r"\d+(?:\.\d+)?",
            value
        )

        if match:

            return max(
                0,
                min(
                    100,
                    int(
                        float(
                            match.group()
                        )
                    )
                )
            )


    return 50


# ============================================================
# ИТОГОВАЯ ОЦЕНКА ДИЗАЙНА
# ============================================================

def calculate_design_score(
    result: AuditResult
) -> int:

    principles = [

        result.composition,
        result.visual_hierarchy,
        result.balance,
        result.contrast,
        result.typography,
        result.color,
        result.negative_space,
        result.alignment,
        result.proximity_grouping,
        result.repetition_rhythm,
        result.unity_coherence,
        result.readability_accessibility,
        result.focal_point,
        result.proportion_scale,

    ]


    scores = []


    for principle in principles:

        if principle.status == (
            "not_applicable"
        ):

            continue

        scores.append(
            normalize_score(
                principle.score
            )
        )


    if not scores:

        return 50


    return round(
        sum(scores) / len(scores)
    )


# ============================================================
# ПРИОРИТЕТНЫЕ ПРОБЛЕМЫ
# ============================================================

def build_priority_issues(
    result: AuditResult
):

    principles = [

        ("Композиция", result.composition),
        ("Визуальная иерархия", result.visual_hierarchy),
        ("Баланс", result.balance),
        ("Контраст", result.contrast),
        ("Типографика", result.typography),
        ("Цвет", result.color),
        ("Негативное пространство", result.negative_space),
        ("Выравнивание", result.alignment),
        ("Близость и группировка", result.proximity_grouping),
        ("Повтор и ритм", result.repetition_rhythm),
        ("Единство и визуальная согласованность", result.unity_coherence),
        ("Читаемость и доступность", result.readability_accessibility),
        ("Фокусная точка", result.focal_point),
        ("Пропорции и масштаб", result.proportion_scale),
        ("Коммуникативная эффективность", result.communication_effectiveness),

    ]


    issues = []


    for name, principle in principles:

        if principle.status == (
            "not_applicable"
        ):

            continue


        score = normalize_score(
            principle.score
        )


        problem = (
            principle.problem
            or ""
        ).strip()


        recommendation = (
            principle.recommendation
            or ""
        ).strip()


        observation = (
            principle.observation
            or ""
        ).strip()


        evidence_list = (
            principle.evidence
            or []
        )


        # Нет проблемы → не создаём карточку

        if not problem:

            continue


        # Высокая оценка → не считаем
        # серьёзной проблемой

        if score >= 80:

            continue


        # Доказательство

        evidence = ""


        if evidence_list:

            evidence = str(
                evidence_list[0]
            ).strip()


        if not evidence:

            evidence = observation


        if not evidence:

            continue


        # Приоритет

        if score < 40:

            priority = "critical"

        elif score < 60:

            priority = "high"

        elif score < 75:

            priority = "medium"

        else:

            priority = "low"


        # Влияние

        perceptual_impact = (
            principle.perceptual_effect
            or ""
        ).strip()


        if not perceptual_impact:

            perceptual_impact = (
                "Проблема может снижать "
                "эффективность визуальной коммуникации."
            )


        # Действие

        action = recommendation


        if not action:

            action = (
                "Скорректировать визуальное решение "
                "с учётом выявленной проблемы."
            )


        # ----------------------------------------------------
        # ВАЖНО:
        # создаём PriorityIssue, а не dict
        # ----------------------------------------------------

        issues.append(
            PriorityIssue(

                priority=priority,

                principle=name,

                issue=problem,

                evidence=evidence,

                perceptual_impact=(
                    perceptual_impact
                ),

                action=action,

            )
        )


    # Сортировка

    priority_order = {

        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,

    }


    issues.sort(
        key=lambda item: (

            priority_order.get(
                item.priority,
                4
            ),

            item.principle,

        )
    )


    # Максимум 5 действительно важных проблем

    return issues[:5]
