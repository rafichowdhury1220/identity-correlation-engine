"""Data models for Identity Correlation Engine"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from uuid import uuid4


class MatchingStrategy(Enum):
    """Matching algorithms available"""
    EXACT = "exact_match"
    FUZZY = "fuzzy_match"
    COMPOSITE = "composite_match"
    ML_BASED = "ml_match"
    HYBRID = "hybrid"


class SourceSystem(Enum):
    """Supported source systems"""
    WORKDAY = "workday"
    ACTIVEDIRECTORY = "activedirectory"
    OKTA = "okta"
    SALESFORCE = "salesforce"
    SAP = "sap"
    CUSTOM = "custom"


@dataclass
class Identity:
    """Represents an identity from a source system
    
    Attributes:
        source: Source system (Workday, AD, Okta, etc.)
        source_id: Unique ID in source system
        first_name: Employee first name
        last_name: Employee last name
        email: Email address
        phone: Phone number
        department: Department
        manager_id: Manager's ID in source system
        attributes: Custom source-specific attributes
    """
    
    source: SourceSystem
    source_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    manager_id: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class MatchingEvidence:
    """Evidence for a matching decision
    
    Attributes:
        strategy: Which matching algorithm was used
        score: Raw matching score (0-1)
        field_scores: Scores per field
        details: Additional matching details
    """
    
    strategy: MatchingStrategy
    score: float
    field_scores: Dict[str, float] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MatchingDecision:
    """Record of a matching decision for audit trail
    
    Attributes:
        id: Unique decision ID
        source_identity_id: First identity ID
        target_identity_id: Second identity ID
        matched: Whether they were matched
        confidence_score: Final confidence (0-100%)
        evidence: List of matching evidence from each strategy
        initiated_by: Who/what initiated this decision
        timestamp: When decision was made
    """
    
    id: str = field(default_factory=lambda: str(uuid4()))
    source_identity_id: str = ""
    target_identity_id: str = ""
    matched: bool = False
    confidence_score: float = 0.0
    evidence: List[MatchingEvidence] = field(default_factory=list)
    initiated_by: str = "system.auto_correlator"
    timestamp: datetime = field(default_factory=datetime.now)
    source_quality_factor: float = 1.0
    historical_accuracy_factor: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "source_identity_id": self.source_identity_id,
            "target_identity_id": self.target_identity_id,
            "matched": self.matched,
            "confidence_score": self.confidence_score,
            "evidence": [
                {
                    "strategy": ev.strategy.value,
                    "score": ev.score,
                    "field_scores": ev.field_scores,
                    "details": ev.details,
                }
                for ev in self.evidence
            ],
            "initiated_by": self.initiated_by,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class UnifiedProfile:
    """Unified identity profile combining data from multiple sources
    
    Attributes:
        id: Unified profile ID
        canonical_email: Primary email (source of truth)
        first_name: Canonical first name
        last_name: Canonical last name
        phone: Primary phone
        department: Department (most recent)
        identities: List of correlated source identities
        confidence_score: Overall confidence (0-100%)
        matched_sources: Which source systems are included
        alternate_ids: Alternative identifiers (jsmith, j.smith, etc.)
        source_attributes: Attributes from each source
        matching_evidence: How we arrived at this profile
        audit_trail: List of matching decisions
    """
    
    id: str = field(default_factory=lambda: str(uuid4()))
    canonical_email: str = ""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    identities: List[Identity] = field(default_factory=list)
    confidence_score: float = 0.0
    matched_sources: List[SourceSystem] = field(default_factory=list)
    alternate_ids: List[str] = field(default_factory=list)
    source_attributes: Dict[SourceSystem, Dict[str, Any]] = field(
        default_factory=dict
    )
    matching_evidence: Dict[str, Any] = field(default_factory=dict)
    audit_trail: List[MatchingDecision] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "canonical_email": self.canonical_email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "department": self.department,
            "identities": [i.to_dict() for i in self.identities],
            "confidence_score": self.confidence_score,
            "matched_sources": [s.value for s in self.matched_sources],
            "alternate_ids": self.alternate_ids,
            "source_attributes": {
                k.value: v for k, v in self.source_attributes.items()
            },
            "matching_evidence": self.matching_evidence,
            "audit_trail": [d.to_dict() for d in self.audit_trail],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class CorrelationResult:
    """Result of correlation process
    
    Attributes:
        unified_profiles: List of merged profiles
        unmatched_identities: Identities that couldn't be correlated
        quality_metrics: Statistics about the correlation
        processing_time_ms: How long it took
    """
    
    unified_profiles: List[UnifiedProfile] = field(default_factory=list)
    unmatched_identities: List[Identity] = field(default_factory=list)
    matching_decisions: List[MatchingDecision] = field(default_factory=list)
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "unified_profiles": [p.to_dict() for p in self.unified_profiles],
            "unmatched_identities": [i.to_dict() for i in self.unmatched_identities],
            "matching_decisions": [d.to_dict() for d in self.matching_decisions],
            "quality_metrics": self.quality_metrics,
            "processing_time_ms": self.processing_time_ms,
        }
