"""Identity matching algorithms"""

from abc import ABC, abstractmethod
from typing import Tuple, List, Dict, Any, Optional
from difflib import SequenceMatcher

from .models import Identity, MatchingStrategy, MatchingEvidence


class BaseMatcher(ABC):
    """Abstract base class for identity matchers"""
    
    @abstractmethod
    def match(self, identity1: Identity, identity2: Identity) -> Tuple[float, List[MatchingEvidence]]:
        """Match two identities
        
        Args:
            identity1: First identity
            identity2: Second identity
        
        Returns:
            Tuple of (score: 0-1, evidence: list of MatchingEvidence)
        """
        pass


class ExactMatcher(BaseMatcher):
    """Exact string matching"""
    
    def match(
        self, identity1: Identity, identity2: Identity
    ) -> Tuple[float, List[MatchingEvidence]]:
        """Exact match on normalized fields
        
        Args:
            identity1: First identity
            identity2: Second identity
        
        Returns:
            Tuple of (score: 0-1, evidence)
        """
        field_scores = {}
        
        # Compare email
        if identity1.email and identity2.email:
            field_scores["email"] = 1.0 if identity1.email == identity2.email else 0.0
        
        # Compare first name
        if identity1.first_name and identity2.first_name:
            field_scores["first_name"] = (
                1.0 if identity1.first_name == identity2.first_name else 0.0
            )
        
        # Compare last name
        if identity1.last_name and identity2.last_name:
            field_scores["last_name"] = (
                1.0 if identity1.last_name == identity2.last_name else 0.0
            )
        
        # Compute overall score
        score = (
            sum(field_scores.values()) / len(field_scores)
            if field_scores
            else 0.0
        )
        
        evidence = [
            MatchingEvidence(
                strategy=MatchingStrategy.EXACT,
                score=score,
                field_scores=field_scores,
                details={"matcher": "exact_string_comparison"},
            )
        ]
        
        return score, evidence


class FuzzyMatcher(BaseMatcher):
    """Fuzzy string matching using Levenshtein distance"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize fuzzy matcher
        
        Args:
            config: Configuration (e.g., threshold)
        """
        self.threshold = config.get("threshold", 0.85)
    
    def match(
        self, identity1: Identity, identity2: Identity
    ) -> Tuple[float, List[MatchingEvidence]]:
        """Fuzzy match on normalized fields
        
        Args:
            identity1: First identity
            identity2: Second identity
        
        Returns:
            Tuple of (score: 0-1, evidence)
        """
        field_scores = {}
        
        # Compare email
        if identity1.email and identity2.email:
            field_scores["email"] = self._string_similarity(
                identity1.email, identity2.email
            )
        
        # Compare first name
        if identity1.first_name and identity2.first_name:
            field_scores["first_name"] = self._string_similarity(
                identity1.first_name, identity2.first_name
            )
        
        # Compare last name
        if identity1.last_name and identity2.last_name:
            field_scores["last_name"] = self._string_similarity(
                identity1.last_name, identity2.last_name
            )
        
        # Compute overall score
        score = (
            sum(field_scores.values()) / len(field_scores)
            if field_scores
            else 0.0
        )
        
        evidence = [
            MatchingEvidence(
                strategy=MatchingStrategy.FUZZY,
                score=score,
                field_scores=field_scores,
                details={
                    "matcher": "levenshtein_distance",
                    "threshold": self.threshold,
                },
            )
        ]
        
        return score, evidence
    
    @staticmethod
    def _string_similarity(str1: str, str2: str) -> float:
        """Calculate similarity between two strings (0-1)
        
        Uses SequenceMatcher ratio
        
        Args:
            str1: First string
            str2: Second string
        
        Returns:
            Similarity score
        """
        if not str1 or not str2:
            return 0.0
        
        return SequenceMatcher(None, str1, str2).ratio()


class CompositeMatcher(BaseMatcher):
    """Multi-field probabilistic matching"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize composite matcher
        
        Args:
            config: Configuration with field weights
        """
        self.field_weights = config.get("field_weights", {
            "email": 0.4,
            "first_name": 0.3,
            "last_name": 0.3,
        })
        self.fuzzy_matcher = FuzzyMatcher(config.get("fuzzy", {}))
    
    def match(
        self, identity1: Identity, identity2: Identity
    ) -> Tuple[float, List[MatchingEvidence]]:
        """Composite match using weighted fields
        
        Args:
            identity1: First identity
            identity2: Second identity
        
        Returns:
            Tuple of (score: 0-1, evidence)
        """
        field_scores = {}
        weighted_sum = 0.0
        total_weight = 0.0
        
        # Compare each field with weight
        comparisons = [
            ("email", identity1.email, identity2.email),
            ("first_name", identity1.first_name, identity2.first_name),
            ("last_name", identity1.last_name, identity2.last_name),
        ]
        
        for field_name, val1, val2 in comparisons:
            if val1 and val2:
                similarity = FuzzyMatcher._string_similarity(val1, val2)
                field_scores[field_name] = similarity
                weight = self.field_weights.get(field_name, 0.0)
                weighted_sum += similarity * weight
                total_weight += weight
        
        # Compute weighted average
        score = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        evidence = [
            MatchingEvidence(
                strategy=MatchingStrategy.COMPOSITE,
                score=score,
                field_scores=field_scores,
                details={
                    "matcher": "weighted_composite",
                    "field_weights": self.field_weights,
                },
            )
        ]
        
        return score, evidence


class HybridMatcher(BaseMatcher):
    """Ensemble matcher combining multiple strategies
    
    Combines:
    - Exact matching (weight: 0.4)
    - Fuzzy matching (weight: 0.3)
    - Composite matching (weight: 0.2)
    - ML model (weight: 0.1) - not implemented yet
    """
    
    def __init__(
        self,
        exact_matcher: ExactMatcher,
        fuzzy_matcher: FuzzyMatcher,
        config: Dict[str, Any],
    ):
        """Initialize hybrid matcher
        
        Args:
            exact_matcher: ExactMatcher instance
            fuzzy_matcher: FuzzyMatcher instance
            config: Configuration with strategy weights
        """
        self.exact_matcher = exact_matcher
        self.fuzzy_matcher = fuzzy_matcher
        self.composite_matcher = CompositeMatcher(config)
        
        strategies = config.get("strategies", [])
        self.weights = {
            MatchingStrategy.EXACT: 0.4,
            MatchingStrategy.FUZZY: 0.3,
            MatchingStrategy.COMPOSITE: 0.2,
            MatchingStrategy.ML_BASED: 0.1,
        }
        
        # Override with config if provided
        for strategy in strategies:
            strategy_name = strategy.get("name")
            if strategy_name == "exact_match":
                self.weights[MatchingStrategy.EXACT] = strategy.get("weight", 0.4)
            elif strategy_name == "fuzzy_match":
                self.weights[MatchingStrategy.FUZZY] = strategy.get("weight", 0.3)
            elif strategy_name == "composite_match":
                self.weights[MatchingStrategy.COMPOSITE] = strategy.get("weight", 0.2)
        
        # Normalize weights
        total_weight = sum(self.weights.values())
        if total_weight > 0:
            for key in self.weights:
                self.weights[key] /= total_weight
    
    def match(
        self, identity1: Identity, identity2: Identity
    ) -> Tuple[float, List[MatchingEvidence]]:
        """Ensemble match using multiple strategies
        
        Args:
            identity1: First identity
            identity2: Second identity
        
        Returns:
            Tuple of (score: 0-1, evidence list)
        """
        all_evidence = []
        weighted_score = 0.0
        
        # Run exact matcher
        exact_score, exact_evidence = self.exact_matcher.match(identity1, identity2)
        all_evidence.extend(exact_evidence)
        weighted_score += exact_score * self.weights[MatchingStrategy.EXACT]
        
        # Run fuzzy matcher
        fuzzy_score, fuzzy_evidence = self.fuzzy_matcher.match(identity1, identity2)
        all_evidence.extend(fuzzy_evidence)
        weighted_score += fuzzy_score * self.weights[MatchingStrategy.FUZZY]
        
        # Run composite matcher
        comp_score, comp_evidence = self.composite_matcher.match(identity1, identity2)
        all_evidence.extend(comp_evidence)
        weighted_score += comp_score * self.weights[MatchingStrategy.COMPOSITE]
        
        # Final score is weighted average
        final_score = weighted_score
        
        return final_score, all_evidence
