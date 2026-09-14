import json
import re

import streamlit as st
from google import genai
from google.genai import types

from prompts import SYSTEM_PROMPT
from schemas import AuditResult


MODEL = "gemini-2.5-flash"


def get_client():
    return genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )


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

    result.overall_design_score = calculate_design_score(
        result
    )

    result.communication_score = normalize_score(
        result.communication_effectiveness.score
    )

    return result


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
предоставленного визуального материала.

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

Верни:

- ровно 3 strengths;
- ровно 3 most_important_problems;
- ровно 3 concrete_recommendations;
- priority_issues;
- improvement_prompt;
- designer_brief.

Не возвращай overall_design_score.

Не возвращай communication_score.

Эти значения рассчитываются программой.

Верни только JSON.
"""


def parse_result(raw_text: str) -> AuditResult:

    cleaned = clean_json_text(
        raw_text
    )

    try:
        data = json.loads(
            cleaned
        )

    except json.JSONDecodeError as error:

        raise ValueError(
            f"Gemini вернул некорректный JSON: {error}"
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


def clean_json_text(text: str) -> str:

    text = text.strip()

    if text.startswith("```"):

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

        if principle.status == "not_applicable":
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


def normalize_score(value) -> int:

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
