from typing import List, Optional

from pydantic import BaseModel, Field


class DesignPrinciple(BaseModel):
    score: int = Field(default=50, ge=0, le=100)
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

    # ========================================================
    # OVERALL SCORES
    # ========================================================

    overall_design_score: int = Field(
        default=50,
        ge=0,
        le=100
    )

    communication_score: int = Field(
        default=50,
        ge=0,
        le=100
    )

    # ========================================================
    # 15 DESIGN PRINCIPLES
    # ========================================================

    composition: DesignPrinciple = Field(
        default_factory=DesignPrinciple
    )

    visual_hierarchy: DesignPrinciple = Field(
        default_factory=DesignPrinciple
    )

    balance: DesignPrinciple = Field(
        default_factory=DesignPrinciple
    )

    contrast: DesignPrinciple = Field(
        default_factory=DesignPrinciple
    )

    typography: DesignPrinciple = Field(
        default_factory=DesignPrinciple
    )

    color: DesignPrinciple = Field(
        default_factory=DesignPrinciple
    )

    negative_space: DesignPrinciple = Field(
        default_factory=DesignPrinciple
    )

    alignment: DesignPrinciple = Field(
        default_factory=DesignPrinciple
    )

    proximity_grouping: DesignPrinciple = Field(
        default_factory=DesignPrinciple
    )

    repetition_rhythm: DesignPrinciple = Field(
        default_factory=DesignPrinciple
    )

    unity_coherence: DesignPrinciple = Field(
        default_factory=DesignPrinciple
    )

    readability_accessibility: DesignPrinciple = Field(
        default_factory=DesignPrinciple
    )

    focal_point: DesignPrinciple = Field(
        default_factory=DesignPrinciple
    )

    proportion_scale: DesignPrinciple = Field(
        default_factory=DesignPrinciple
    )

    communication_effectiveness: DesignPrinciple = Field(
        default_factory=DesignPrinciple
    )

    # ========================================================
    # SYNTHESIS
    # ========================================================

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
