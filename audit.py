import json
import re
from typing import Any

import streamlit as st
from google import genai
from google.genai import types

from prompts import SYSTEM_PROMPT
from schemas import AuditResult


# ============================================================
# MODEL
# ============================================================

MODEL = "gemini-3.5-flash-lite"


# ============================================================
# CLIENT
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
) -> AuditResult:

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
            temperature=0.15
        )
    )

    if not response.text:
        raise ValueError(
            "Gemini не вернул результат."
        )

    return parse_result(
        response.text
    )


# ============================================================
# USER PROMPT
# ============================================================

def build_user_prompt(
    communication_goal: str = "",
    target_action: str = ""
) -> str:

    if not communication_goal.strip():
        communication_goal = (
            "Коммуникативная задача не задана пользователем. "
            "Определи предполагаемую задачу только на основании "
            "видимого содержания изображения."
        )

    if not target_action.strip():
        target_action = (
            "Целевое действие не задано пользователем. "
            "Если оно действительно предполагается из изображения, "
            "определи его осторожно."
        )

    return f"""
Проведи профессиональный визуальный аудит
предоставленного изображения.

============================================================
КОММУНИКАТИВНАЯ ЗАДАЧА
============================================================

{communication_goal}

============================================================
ЦЕЛЕВОЕ ДЕЙСТВИЕ
============================================================

{target_action}

============================================================
ТРЕБОВАНИЯ
============================================================

Проанализируй изображение по всем 15 критериям.

Для каждого критерия обязательно верни:

score
status
observation
evidence
rationale
perceptual_effect
problem
recommendation
score_justification

Поле evidence ОБЯЗАТЕЛЬНО должно быть массивом строк.

Например:

"evidence": [
    "Заголовок занимает верхнюю треть изображения.",
    "Дата размещена значительно ниже названия."
]

Если существенной проблемы нет:

"problem": null

Если рекомендация не требуется:

"recommendation": null

Но остальные содержательные поля всё равно должны
объяснять, почему решение работает.

============================================================
КАЧЕСТВО АНАЛИЗА
============================================================

Не ограничивайся описанием.

Нужно объяснить связь:

что видно
→ почему это относится к принципу
→ как это влияет на восприятие
→ почему оценка именно такая
→ что следует изменить.

Не придумывай:

- размеры, которых невозможно оценить;
- информацию, которой нет;
- намерения автора;
- брендовые требования;
- целевую аудиторию, если она не указана
  и не следует очевидно из изображения.

============================================================
ОБЩИЕ РЕЗУЛЬТАТЫ
============================================================

Верни:

overall_design_score
communication_score

priority_issues
strengths
most_important_problems
concrete_recommendations
improvement_prompt
designer_brief

strengths — ровно 3.

most_important_problems — ровно 3.

concrete_recommendations — ровно 3.

priority_issues — максимум 5.
Не создавай пустые объекты.

============================================================
ЯЗЫК
============================================================

Весь содержательный текст должен быть
ТОЛЬКО НА РУССКОМ ЯЗЫКЕ.

Английские технические ключи JSON
оставляй без изменений.

Значения priority:

critical
high
medium
low

также оставляй на английском.

Текст, присутствующий непосредственно
на изображении, не переводи.

============================================================
REDESIGN
============================================================

В improvement_prompt обязательно объясни:

- что сохранить;
- что изменить;
- какую иерархию установить;
- какие элементы сделать крупнее или меньше;
- как организовать информационные блоки;
- что сделать с цветом;
- что сделать с типографикой;
- как использовать свободное пространство.

Если исходная композиция неэффективна,
разрешается полностью её перестроить.

Главный принцип:

"Сохрани содержание, но перестрой дизайн."

Верни только JSON.
"""


# ============================================================
# PARSING
# ============================================================

def parse_result(raw_text: str) -> AuditResult:

    raw_text = clean_json_text(
        raw_text
    )

    try:

        data = json.loads(
            raw_text
        )

    except json.JSONDecodeError as error:

        raise ValueError(
            f"Gemini вернул некорректный JSON: {error}"
        )

    normalized = normalize_data(
        data
    )

    try:

        return AuditResult.model_validate(
            normalized
        )

    except Exception as error:

        raise ValueError(
            f"Не удалось обработать результат Gemini: {error}"
        )


# ============================================================
# CLEAN JSON
# ============================================================

def clean_json_text(
    text: str
) -> str:

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


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_data(
    data: Any
) -> dict:

    if not isinstance(data, dict):
        data = {}

    result = {}

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
        "communication_effectiveness"
    ]

    for name in principle_names:

        found = find_principle(
            data,
            name
        )

        result[name] = normalize_principle(
            found
        )

    result["overall_design_score"] = normalize_score(
        find_value(
            data,
            [
                "overall_design_score",
                "design_score",
                "overall_score"
            ],
            50
        )
    )

    result["communication_score"] = normalize_score(
        find_value(
            data,
            [
                "communication_score",
                "communication_effectiveness_score",
                "communication"
            ],
            50
        )
    )

    priority_data = find_value(
        data,
        [
            "priority_issues",
            "priorities",
            "critical_issues"
        ],
        []
    )

    result["priority_issues"] = normalize_priority_issues(
        priority_data
    )

    strengths = find_value(
        data,
        [
            "strengths",
            "strengths_of_design"
        ],
        []
    )

    result["strengths"] = normalize_list(
        strengths,
        [
            "strength",
            "description",
            "text"
        ]
    )[:3]

    problems = find_value(
        data,
        [
            "most_important_problems",
            "main_problems",
            "key_problems"
        ],
        []
    )

    result["most_important_problems"] = normalize_list(
        problems,
        [
            "problem",
            "issue",
            "description",
            "text"
        ]
    )[:3]

    recommendations = find_value(
        data,
        [
            "concrete_recommendations",
            "recommendations",
            "actions"
        ],
        []
    )

    result["concrete_recommendations"] = normalize_list(
        recommendations,
        [
            "recommendation",
            "action",
            "description",
            "text"
        ]
    )[:3]

    result["improvement_prompt"] = normalize_string(
        find_value(
            data,
            [
                "improvement_prompt",
                "redesign_prompt",
                "design_prompt"
            ],
            ""
        )
    )

    result["designer_brief"] = normalize_string(
        find_value(
            data,
            [
                "designer_brief",
                "design_brief",
                "brief"
            ],
            ""
        )
    )

    return result


# ============================================================
# FIND PRINCIPLE
# ============================================================

def find_principle(
    data: dict,
    target: str
):

    if target in data:
        return data[target]

    aliases = {

        "composition": [
            "composition",
            "композиция"
        ],

        "visual_hierarchy": [
            "visual_hierarchy",
            "hierarchy",
            "визуальная иерархия",
            "иерархия"
        ],

        "balance": [
            "balance",
            "баланс"
        ],

        "contrast": [
            "contrast",
            "контраст"
        ],

        "typography": [
            "typography",
            "типографика"
        ],

        "color": [
            "color",
            "colour",
            "цвет"
        ],

        "negative_space": [
            "negative_space",
            "whitespace",
            "negative space",
            "негативное пространство"
        ],

        "alignment": [
            "alignment",
            "выравнивание"
        ],

        "proximity_grouping": [
            "proximity_grouping",
            "proximity",
            "grouping",
            "близость и группировка",
            "близость",
            "группировка"
        ],

        "repetition_rhythm": [
            "repetition_rhythm",
            "repetition",
            "rhythm",
            "повтор и ритм",
            "повтор",
            "ритм"
        ],

        "unity_coherence": [
            "unity_coherence",
            "unity",
            "coherence",
            "единство и визуальная согласованность",
            "единство",
            "согласованность"
        ],

        "readability_accessibility": [
            "readability_accessibility",
            "readability",
            "accessibility",
            "читаемость и доступность",
            "читаемость",
            "доступность"
        ],

        "focal_point": [
            "focal_point",
            "focal",
            "focus",
            "фокусная точка",
            "фокус"
        ],

        "proportion_scale": [
            "proportion_scale",
            "proportion",
            "scale",
            "пропорции и масштаб",
            "пропорции",
            "масштаб"
        ],

        "communication_effectiveness": [
            "communication_effectiveness",
            "communication",
            "communicative_effectiveness",
            "коммуникативная эффективность",
            "коммуникация"
        ]
    }

    wanted = aliases.get(
        target,
        []
    )

    for key, value in data.items():

        normalized_key = normalize_name(
            key
        )

        for alias in wanted:

            if normalized_key == normalize_name(
                alias
            ):

                return value

    # Дополнительный поиск по объектам
    for value in data.values():

        if isinstance(
            value,
            dict
        ):

            principle_value = value.get(
                "principle"
            )

            if principle_value:

                if normalize_name(
                    principle_value
                ) in {
                    normalize_name(alias)
                    for alias in wanted
                }:

                    return value

            name_value = value.get(
                "name"
            )

            if name_value:

                if normalize_name(
                    name_value
                ) in {
                    normalize_name(alias)
                    for alias in wanted
                }:

                    return value

    return {}


# ============================================================
# NORMALIZE PRINCIPLE
# ============================================================

def normalize_principle(
    item
) -> dict:

    if not isinstance(
        item,
        dict
    ):

        item = {}

    evidence = item.get(
        "evidence",
        []
    )

    if isinstance(
        evidence,
        str
    ):

        evidence = [
            evidence
        ]

    elif isinstance(
        evidence,
        dict
    ):

        evidence = [
            normalize_string(
                evidence
            )
        ]

    elif not isinstance(
        evidence,
        list
    ):

        evidence = []

    evidence = [
        normalize_string(
            value
        )
        for value in evidence
        if normalize_string(
            value
        ).strip()
    ]

    return {

        "score": normalize_score(
            item.get(
                "score",
                50
            )
        ),

        "status": normalize_string(
            item.get(
                "status",
                "applicable"
            )
        ),

        "observation": normalize_string(
            item.get(
                "observation",
                item.get(
                    "what_is_visible",
                    ""
                )
            )
        ),

        "evidence": evidence,

        "rationale": normalize_string(
            item.get(
                "rationale",
                item.get(
                    "why_it_matters",
                    ""
                )
            )
        ),

        "perceptual_effect": normalize_string(
            item.get(
                "perceptual_effect",
                item.get(
                    "impact",
                    item.get(
                        "perceptual_impact",
                        ""
                    )
                )
            )
        ),

        "problem": normalize_optional_string(
            item.get(
                "problem",
                item.get(
                    "issue",
                    None
                )
            )
        ),

        "recommendation": normalize_optional_string(
            item.get(
                "recommendation",
                item.get(
                    "action",
                    None
                )
            )
        ),

        "score_justification": normalize_string(
            item.get(
                "score_justification",
                item.get(
                    "score_reason",
                    item.get(
                        "reason",
                        ""
                    )
                )
            )
        )
    }


# ============================================================
# PRIORITY ISSUES
# ============================================================

def normalize_priority_issues(
    items
) -> list:

    if not isinstance(
        items,
        list
    ):

        if isinstance(
            items,
            dict
        ):

            items = [
                items
            ]

        else:

            return []

    result = []

    allowed_priorities = {
        "critical",
        "high",
        "medium",
        "low"
    }

    for item in items:

        if not isinstance(
            item,
            dict
        ):

            continue

        priority = normalize_string(
            item.get(
                "priority",
                item.get(
                    "severity",
                    "medium"
                )
            )
        ).lower()

        if priority not in allowed_priorities:
            priority = "medium"

        principle = normalize_string(
            item.get(
                "principle",
                item.get(
                    "principle_name",
                    ""
                )
            )
        )

        issue = normalize_string(
            item.get(
                "issue",
                item.get(
                    "problem",
                    ""
                )
            )
        )

        evidence = normalize_string(
            item.get(
                "evidence",
                ""
            )
        )

        impact = normalize_string(
            item.get(
                "perceptual_impact",
                item.get(
                    "impact",
                    ""
                )
            )
        )

        action = normalize_string(
            item.get(
                "action",
                item.get(
                    "recommendation",
                    ""
                )
            )
        )

        # Не добавляем пустые карточки
        if not (
            principle.strip()
            and issue.strip()
            and evidence.strip()
            and impact.strip()
            and action.strip()
        ):

            continue

        result.append(
            {
                "priority": priority,
                "principle": principle,
                "issue": issue,
                "evidence": evidence,
                "perceptual_impact": impact,
                "action": action
            }
        )

    # Максимум 5 проблем
    return result[:5]


# ============================================================
# LIST NORMALIZATION
# ============================================================

def normalize_list(
    value,
    preferred_keys
) -> list:

    if value is None:
        return []

    if isinstance(
        value,
        str
    ):

        if value.strip():
            return [
                value.strip()
            ]

        return []

    if isinstance(
        value,
        dict
    ):

        value = [
            value
        ]

    if not isinstance(
        value,
        list
    ):

        return [
            normalize_string(
                value
            )
        ]

    result = []

    for item in value:

        if isinstance(
            item,
            str
        ):

            if item.strip():
                result.append(
                    item.strip()
                )

            continue

        if isinstance(
            item,
            dict
        ):

            text = ""

            for key in preferred_keys:

                if key in item:

                    text = normalize_string(
                        item[key]
                    )

                    if text.strip():
                        break

            if not text:

                text = normalize_string(
                    item
                )

            if text.strip():
                result.append(
                    text
                )

        else:

            text = normalize_string(
                item
            )

            if text.strip():
                result.append(
                    text
                )

    return result


# ============================================================
# FIND VALUE
# ============================================================

def find_value(
    data,
    keys,
    default=None
):

    normalized_keys = {
        normalize_name(key)
        for key in keys
    }

    for key, value in data.items():

        if normalize_name(
            key
        ) in normalized_keys:

            return value

    return default


# ============================================================
# STRING NORMALIZATION
# ============================================================

def normalize_string(
    value
) -> str:

    if value is None:
        return ""

    if isinstance(
        value,
        str
    ):

        return value.strip()

    if isinstance(
        value,
        dict
    ):

        preferred_keys = [
            "text",
            "description",
            "content",
            "summary",
            "brief",
            "value",
            "action",
            "recommendation",
            "problem",
            "issue",
            "strength"
        ]

        for key in preferred_keys:

            if key in value:

                text = normalize_string(
                    value[key]
                )

                if text.strip():
                    return text

        parts = []

        for key, item in value.items():

            text = normalize_string(
                item
            )

            if text.strip():

                parts.append(
                    f"{key}: {text}"
                )

        return "\n".join(
            parts
        )

    if isinstance(
        value,
        list
    ):

        return "\n".join(
            normalize_string(
                item
            )
            for item in value
        )

    return str(value)


# ============================================================
# OPTIONAL STRING
# ============================================================

def normalize_optional_string(
    value
):

    if value is None:
        return None

    text = normalize_string(
        value
    )

    if not text.strip():
        return None

    return text


# ============================================================
# SCORE
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
# NAME
# ============================================================

def normalize_name(
    name
) -> str:

    return (
        str(name)
        .lower()
        .strip()
        .replace(
            " ",
            "_"
        )
        .replace(
            "-",
            "_"
        )
        .replace(
            "/",
            "_"
        )
    )
