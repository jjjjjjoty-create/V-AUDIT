from typing import List, Optional
from pydantic import BaseModel, Field


class DesignPrinciple(BaseModel):
    score: int = 50
    status: str = "applicable"

    observation: str = ""
    evidence: List[str] = Field(default_factory=list)

    rationale: str = ""
    perceptual_effect: str = ""

    problem: Optional[str] = None
    recommendation: Optional[str] = None

    score_justification: str = ""


class PriorityIssue(BaseModel):
    priority: str = "medium"
    principle: str = ""
    issue: str = ""
    evidence: str = ""
    perceptual_impact: str = ""
    action: str = ""


class AuditResult(BaseModel):

    # Итоговые показатели рассчитываются программно
    overall_design_score: int = 50
    communication_score: int = 50

    # 1. Композиционная организация
    composition: DesignPrinciple = Field(default_factory=DesignPrinciple)
    balance: DesignPrinciple = Field(default_factory=DesignPrinciple)
    proportion_scale: DesignPrinciple = Field(default_factory=DesignPrinciple)

    # 2. Иерархия и внимание
    visual_hierarchy: DesignPrinciple = Field(default_factory=DesignPrinciple)
    focal_point: DesignPrinciple = Field(default_factory=DesignPrinciple)
    contrast: DesignPrinciple = Field(default_factory=DesignPrinciple)

    # 3. Пространственная организация
    negative_space: DesignPrinciple = Field(default_factory=DesignPrinciple)
    alignment: DesignPrinciple = Field(default_factory=DesignPrinciple)
    proximity_grouping: DesignPrinciple = Field(default_factory=DesignPrinciple)

    # 4. Визуальные средства
    typography: DesignPrinciple = Field(default_factory=DesignPrinciple)
    color: DesignPrinciple = Field(default_factory=DesignPrinciple)
    readability_accessibility: DesignPrinciple = Field(
        default_factory=DesignPrinciple
    )

    # 5. Целостность и коммуникация
    repetition_rhythm: DesignPrinciple = Field(
        default_factory=DesignPrinciple
    )
    unity_coherence: DesignPrinciple = Field(
        default_factory=DesignPrinciple
    )
    communication_effectiveness: DesignPrinciple = Field(
        default_factory=DesignPrinciple
    )

    # Итоговые результаты
    priority_issues: List[PriorityIssue] = Field(
        default_factory=list
    )

    strengths: List[str] = Field(
        default_factory=list
    )

    most_important_problems: List[str] = Field(
        default_factory=list
    )

    concrete_recommendations: List[str] = Field(
        default_factory=list
    )

    improvement_prompt: str = ""

    designer_brief: str = ""
