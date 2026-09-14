import json
import re

import streamlit as st
from google import genai
from google.genai import types

from prompts import SYSTEM_PROMPT
from schemas import AuditResult


MODEL = "gemini-2.5-flash"


# ============================================================
# GEMINI CLIENT
# ============================================================

def get_client():

    return genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )


# ============================================================
# MAIN ANALYSIS
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

    # --------------------------------------------------------
    # Получаем JSON
    # --------------------------------------------------------

    result = parse_result(
        response.text
    )

    # --------------------------------------------------------
    # Рассчитываем итоговые показатели
    # --------------------------------------------------------

    result.overall_design_score = (
        calculate_design_score(result)
    )

    result.communication_score = (
        normalize_score(
            result.communication_effectiveness.score
        )
    )

    return result


# ============================================================
# USER PROMPT
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
Проведи полный структурированный аудит
предоставленного графического материала.

КОММУНИКАТИВНАЯ ЗАДАЧА:
{goal}

ПРЕДПОЛАГАЕМОЕ ДЕЙСТВИЕ ЗРИТЕЛЯ:
{action}

Если коммуникативная задача или действие
не предоставлены, не придумывай их.

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

Для evidence допустимы как одна конкретная
строка-доказательство, так и список доказательств.

Верни:

- ровно 3 strengths;
- ровно 3 most_important_problems;
- ровно 3 concrete_recommendations;
- priority_issues;
- improvement_prompt;
- designer_brief.

designer_brief может быть как обычным текстом,
так и структурированным объектом.

Не возвращай:

overall_design_score
communication_score

Эти показатели рассчитываются программой.

Не добавляй никаких комментариев
вне JSON.

Верни только JSON.
"""


# ============================================================
# PARSE GEMINI RESULT
# ============================================================

def parse_result(raw_text: str):

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

    # --------------------------------------------------------
    # Нормализуем ответ ДО Pydantic
    # --------------------------------------------------------

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
# NORMALIZATION
# ============================================================

def normalize_result_data(
    data: dict
):

    principle_names = [

        "composition",
        "balance",
        "proportion_scale",

        "visual_hierarchy",
        "focal_point",
        "contrast",

        "negative_space",
        "alignment",
        "proximity_grouping",

        "typography",
        "color",
        "readability_accessibility",

        "repetition_rhythm",
        "unity_coherence",
        "communication_effectiveness",
    ]


    # --------------------------------------------------------
    # Нормализуем 15 принципов
    # --------------------------------------------------------

    for name in principle_names:

        principle = data.get(name)

        if not isinstance(
            principle,
            dict
        ):
            continue


        # ====================================================
        # SCORE
        # ====================================================

        principle["score"] = normalize_score(
            principle.get(
                "score",
                50
            )
        )


        # ====================================================
        # STATUS
        # ====================================================

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


        # ====================================================
        # EVIDENCE
        # ====================================================

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


        # ====================================================
        # TEXT FIELDS
        # ====================================================

        text_fields = [

            "observation",
            "rationale",
            "perceptual_effect",
            "score_justification",
        ]

        for field in text_fields:

            value = principle.get(
                field,
                ""
            )

            principle[field] = (
                convert_to_text(value)
            )


        # ====================================================
        # OPTIONAL FIELDS
        # ====================================================

        for field in [
            "problem",
            "recommendation"
        ]:

            value = principle.get(
                field
            )

            if value is None:

                principle[field] = None

            else:

                principle[field] = (
                    convert_to_text(value)
                )


    # ========================================================
    # PRIORITY ISSUES
    # ========================================================

    priority_issues = data.get(
        "priority_issues",
        []
    )

    if not isinstance(
        priority_issues,
        list
    ):

        priority_issues = []

    normalized_issues = []

    for issue in priority_issues:

        if not isinstance(
            issue,
            dict
        ):
            continue

        normalized_issues.append({

            "priority": convert_to_text(
                issue.get(
                    "priority",
                    "medium"
                )
            ),

            "principle": convert_to_text(
                issue.get(
                    "principle",
                    ""
                )
            ),

            "issue": convert_to_text(
                issue.get(
                    "issue",
                    ""
                )
            ),

            "evidence": convert_to_text(
                issue.get(
                    "evidence",
                    ""
                )
            ),

            "perceptual_impact": convert_to_text(
                issue.get(
                    "perceptual_impact",
                    ""
                )
            ),

            "action": convert_to_text(
                issue.get(
                    "action",
                    ""
                )
            )
        })

    data["priority_issues"] = normalized_issues


    # ========================================================
    # LISTS
    # ========================================================

    for field in [
        "strengths",
        "most_important_problems",
        "concrete_recommendations"
    ]:

        value = data.get(
            field,
            []
        )

        if isinstance(
            value,
            list
        ):

            data[field] = [
                convert_to_text(item)
                for item in value
            ]

        elif value:

            data[field] = [
                convert_to_text(value)
            ]

        else:

            data[field] = []


    # ========================================================
    # IMPROVEMENT PROMPT
    # ========================================================

    data["improvement_prompt"] = (
        convert_to_text(
            data.get(
                "improvement_prompt",
                ""
            )
        )
    )


    # ========================================================
    # DESIGNER BRIEF
    # ========================================================

    data["designer_brief"] = (
        convert_to_text(
            data.get(
                "designer_brief",
                ""
            )
        )
    )


    return data


# ============================================================
# CONVERT ANY VALUE TO TEXT
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
# CLEAN JSON
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
# SCORE NORMALIZATION
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
# DESIGN SCORE
# ============================================================

def calculate_design_score(
    result: AuditResult
) -> int:

    principles = [

        result.composition,
        result.balance,
        result.proportion_scale,

        result.visual_hierarchy,
        result.focal_point,
        result.contrast,

        result.negative_space,
        result.alignment,
        result.proximity_grouping,

        result.typography,
        result.color,
        result.readability_accessibility,

        result.repetition_rhythm,
        result.unity_coherence,
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
