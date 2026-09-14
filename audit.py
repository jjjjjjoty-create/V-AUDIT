import json
import re

import streamlit as st
from google import genai
from google.genai import types

from prompts import SYSTEM_PROMPT
from schemas import AuditResult, PriorityIssue


# ============================================================
# НАСТРОЙКИ
# ============================================================

MODEL = "gemini-2.5-flash-lite"


# ============================================================
# ПОДКЛЮЧЕНИЕ GEMINI
# ============================================================

def get_client():

    return genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )


# ============================================================
# ОСНОВНОЙ АНАЛИЗ ИЗОБРАЖЕНИЯ
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
            "Gemini не вернул результат анализа."
        )

    result = parse_result(
        response.text
    )

    # ========================================================
    # ИТОГОВЫЕ ОЦЕНКИ
    # ========================================================

    result.overall_design_score = (
        calculate_design_score(result)
    )

    result.communication_score = (
        normalize_score(
            result.communication_effectiveness.score
        )
    )

    # ========================================================
    # ПРИОРИТЕТНЫЕ ПРОБЛЕМЫ
    # ========================================================

    result.priority_issues = (
        build_priority_issues(result)
    )

    return result


# ============================================================
# ПРОМПТ
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


============================================================
ОСНОВНАЯ ЗАДАЧА
============================================================

Проанализируй изображение по всем 15 критериям
графического дизайна.

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


============================================================
ЯЗЫК РЕЗУЛЬТАТА
============================================================

ВЕСЬ РЕЗУЛЬТАТ ДОЛЖЕН БЫТЬ ТОЛЬКО НА РУССКОМ ЯЗЫКЕ.

Это относится ко всем текстовым полям:

- observation
- evidence
- rationale
- perceptual_effect
- problem
- recommendation
- score_justification
- strengths
- most_important_problems
- concrete_recommendations
- improvement_prompt
- designer_brief

НЕ используй английский язык в этих полях.

Если на изображении присутствует текст,
сохраняй его в оригинальном виде.

Например:

«Школьная новогодняя ёлка»
«2027»

Названия элементов изображения не переводи,
если они являются текстом, непосредственно
присутствующим на изображении.


============================================================
ЛОГИЧЕСКАЯ СОГЛАСОВАННОСТЬ
============================================================

Для каждого критерия поля:

observation
evidence
problem
score_justification
recommendation

должны быть логически согласованы между собой.

Доказательство должно подтверждать именно ту проблему,
которая указана в поле problem.

Нельзя указывать доказательство, которое противоречит
описанной проблеме.

Например:

Если evidence говорит, что элементы хорошо сгруппированы,
нельзя одновременно писать, что они плохо сгруппированы,
если нет дополнительного конкретного доказательства.

Если конкретной проблемы не обнаружено:

problem = null
recommendation = null

Не создавай искусственные проблемы только для того,
чтобы заполнить все 15 критериев.


============================================================
ВИЗУАЛЬНЫЕ ДОКАЗАТЕЛЬСТВА
============================================================

Каждое доказательство должно описывать конкретный
визуально наблюдаемый элемент.

Не используй абстрактные утверждения без визуального основания.

Плохо:

«Дизайн выглядит непрофессионально».

Хорошо:

«Основной заголовок занимает значительно меньшую
площадь, чем декоративный элемент «2027», поэтому
информационная иерархия смещается в пользу декоративного
элемента».

НЕ придумывай элементы, которых нет на изображении.

Если элемент невозможно достоверно определить,
не утверждай его наличие.


============================================================
ОЦЕНКА
============================================================

Используй шкалу от 0 до 100.

90–100:
принцип реализован исключительно хорошо.

80–89:
принцип реализован хорошо, существенных проблем нет.

70–79:
есть небольшие недостатки.

60–69:
заметные недостатки, влияющие на качество.

40–59:
существенная проблема.

20–39:
серьёзная проблема.

0–19:
критическое нарушение принципа.

Оценка должна соответствовать фактическому
качеству изображения.

Не занижай оценку только для того, чтобы создать
приоритетную проблему.

Не повышай оценку только для того, чтобы изображение
выглядело лучше.


============================================================
СТАТУС КРИТЕРИЯ
============================================================

Используй:

applicable
если критерий можно полноценно оценить.

limited
если критерий можно оценить только частично.

not_applicable
если критерий объективно неприменим
к данному изображению.

Если критерий имеет статус not_applicable,
не создавай для него проблему.


============================================================
15 КРИТЕРИЕВ
============================================================

1. Композиция

Оцени расположение и взаимодействие основных
визуальных элементов в пределах формата.


2. Визуальная иерархия

Оцени порядок, в котором зритель воспринимает
информацию по степени важности.


3. Баланс

Оцени распределение визуального веса элементов
по площади композиции.


4. Контраст

Оцени различия по размеру, цвету, светлоте,
насыщенности, форме и другим визуальным параметрам.


5. Типографика

Оцени выбор, размер, начертание, интерлиньяж,
длину строк и сочетание шрифтов.


6. Цвет

Оцени цветовую палитру, сочетание цветов,
контрастность и соответствие коммуникативной задаче.


7. Негативное пространство

Оцени свободное пространство вокруг и между
элементами и его роль в структуре композиции.


8. Выравнивание

Оцени наличие визуальных осей, сетки и согласованности
расположения элементов.


9. Близость и группировка

Оцени, правильно ли связанные элементы расположены
рядом и воспринимаются как единые информационные блоки.


10. Повтор и ритм

Оцени повторение форм, цветов, размеров,
графических элементов и других визуальных признаков.


11. Единство и визуальная согласованность

Оцени, воспринимаются ли все элементы как части
одной визуальной системы.


12. Читаемость и доступность

Оцени возможность быстро и без лишнего усилия
прочитать и понять информацию.


13. Фокусная точка

Оцени наличие главного визуального центра
и его соответствие основной задаче сообщения.


14. Пропорции и масштаб

Оцени соотношение размеров элементов между собой
и относительно формата.


15. Коммуникативная эффективность

Оцени, насколько дизайн эффективно передаёт
основное сообщение и помогает зрителю понять,
что нужно узнать или сделать.


============================================================
ВАЖНО ДЛЯ КОММУНИКАТИВНОЙ ЭФФЕКТИВНОСТИ
============================================================

Если коммуникативная задача не предоставлена,
не придумывай конкретное целевое действие.

В этом случае оценивай только то,
что непосредственно следует из изображения:

- что является основным сообщением;
- насколько быстро оно считывается;
- насколько легко найти ключевую информацию;
- нет ли препятствий для понимания.


============================================================
ДОПОЛНИТЕЛЬНЫЕ РЕЗУЛЬТАТЫ
============================================================

Верни:

strengths

Список сильных сторон дизайна.

most_important_problems

Три наиболее существенные проблемы.

concrete_recommendations

Три наиболее конкретные рекомендации.


============================================================
ПРОМПТ ДЛЯ РЕДИЗАЙНА
============================================================

Сформируй improvement_prompt.

Он должен быть конкретным техническим заданием
для генератора изображений или дизайнера.

Он должен учитывать реальные проблемы,
выявленные в аудите.

Не ограничивайся фразами:

«сделать красивее»
«улучшить дизайн»
«сделать современнее».

Указывай конкретно:

- композицию;
- иерархию;
- размеры;
- группировку;
- типографику;
- цвет;
- негативное пространство;
- расположение элементов;
- приоритет информации.

Если исходная композиция существенно неудачна,
разрешается полностью перестроить её.


============================================================
DESIGNER BRIEF
============================================================

Сформируй designer_brief как профессиональное
техническое задание дизайнеру.

Он должен содержать:

- цель;
- основное сообщение;
- визуальную иерархию;
- ключевые элементы;
- рекомендации по композиции;
- рекомендации по типографике;
- рекомендации по цвету;
- рекомендации по пространству;
- ограничения.

Все пункты должны основываться на проведённом анализе.


============================================================
PRIORITY ISSUES
============================================================

НЕ формируй priority_issues.

Они будут рассчитаны программой автоматически
на основании качества принципов и обнаруженных проблем.


============================================================
ОБЩИЕ ОГРАНИЧЕНИЯ
============================================================

Не придумывай факты.

Не придумывай элементы изображения.

Не создавай искусственные проблемы.

Не повторяй одну и ту же проблему под разными
названиями критериев, если она относится
к одному и тому же визуальному нарушению.

Не используй английский язык в текстовых результатах.

Не добавляй комментариев вне JSON.

Верни только JSON.
"""


# ============================================================
# РАЗБОР JSON
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
# НОРМАЛИЗАЦИЯ РЕЗУЛЬТАТА
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


    # ========================================================
    # ПРИНЦИПЫ
    # ========================================================

    for name in principle_names:

        principle = data.get(
            name
        )


        if not isinstance(
            principle,
            dict
        ):

            principle = {}

            data[name] = principle


        # SCORE

        principle["score"] = (
            normalize_score(
                principle.get(
                    "score",
                    50
                )
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
            "not_applicable",

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

            principle[field] = (
                convert_to_text(
                    principle.get(
                        field,
                        ""
                    )
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

                converted = (
                    convert_to_text(
                        value
                    )
                )


                if converted.strip():

                    principle[field] = converted

                else:

                    principle[field] = None


    # ========================================================
    # СПИСКИ
    # ========================================================

    data["strengths"] = (
        normalize_string_list(
            data.get(
                "strengths",
                []
            )
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


    # ========================================================
    # PROMPT
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


    # Gemini priority_issues не используем

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

                item_text = str(
                    item
                )


            parts.append(

                f"{readable_key}: {item_text}"

            )


        return "\n".join(
            parts
        )


    return str(
        value
    )


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


    text = convert_to_text(
        value
    )


    if text.strip():

        return [
            text
        ]


    return []


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

            text,

            flags=re.IGNORECASE

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
# ФОРМИРОВАНИЕ ПРИОРИТЕТНЫХ ПРОБЛЕМ
# ============================================================

def build_priority_issues(
    result: AuditResult
):

    principles = [

        (
            "Композиция",
            result.composition
        ),

        (
            "Визуальная иерархия",
            result.visual_hierarchy
        ),

        (
            "Баланс",
            result.balance
        ),

        (
            "Контраст",
            result.contrast
        ),

        (
            "Типографика",
            result.typography
        ),

        (
            "Цвет",
            result.color
        ),

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

        (
            "Повтор и ритм",
            result.repetition_rhythm
        ),

        (
            "Единство и визуальная согласованность",
            result.unity_coherence
        ),

        (
            "Читаемость и доступность",
            result.readability_accessibility
        ),

        (
            "Фокусная точка",
            result.focal_point
        ),

        (
            "Пропорции и масштаб",
            result.proportion_scale
        ),

        (
            "Коммуникативная эффективность",
            result.communication_effectiveness
        ),

    ]


    issues = []


    for name, principle in principles:

        # ----------------------------------------------------
        # Неприменимый критерий
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # НЕТ ПРОБЛЕМЫ
        # ----------------------------------------------------

        if not problem:

            continue


        # ----------------------------------------------------
        # Высокая оценка
        # ----------------------------------------------------

        if score >= 80:

            continue


        # ----------------------------------------------------
        # Получаем доказательство
        # ----------------------------------------------------

        evidence = ""


        if evidence_list:

            evidence = str(

                evidence_list[0]

            ).strip()


        if not evidence:

            evidence = observation


        if not evidence:

            continue


        # ----------------------------------------------------
        # Приоритет
        # ----------------------------------------------------

        if score < 40:

            priority = "critical"


        elif score < 60:

            priority = "high"


        elif score < 75:

            priority = "medium"


        else:

            priority = "low"


        # ----------------------------------------------------
        # Влияние
        # ----------------------------------------------------

        perceptual_impact = (

            principle.perceptual_effect

            or ""

        ).strip()


        if not perceptual_impact:

            perceptual_impact = (

                "Проблема может снижать "
                "эффективность визуальной коммуникации."

            )


        # ----------------------------------------------------
        # Рекомендация
        # ----------------------------------------------------

        action = recommendation


        if not action:

            action = (

                "Скорректировать визуальное решение "
                "с учётом выявленной проблемы."

            )


        # ----------------------------------------------------
        # Создаём Pydantic-объект
        # ----------------------------------------------------

        issue = PriorityIssue(

            priority=priority,

            principle=name,

            issue=problem,

            evidence=evidence,

            perceptual_impact=perceptual_impact,

            action=action,

        )


        issues.append(
            issue
        )


    # ========================================================
    # СОРТИРОВКА
    # ========================================================

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

            item.score if hasattr(
                item,
                "score"
            )
            else 0,

        )

    )


    # ========================================================
    # МАКСИМУМ 5 ПРОБЛЕМ
    # ========================================================

    return issues[:5]
