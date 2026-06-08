"""Core Identity Correlator - Main orchestration engine"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from dataclasses import field

from .models import (
    Identity,
    SourceSystem,
    UnifiedProfile,
    MatchingDecision,
    MatchingStrategy,
    MatchingEvidence,
    CorrelationResult,
)
from .normalizers import TextNormalizer
from .matchers import ExactMatcher, FuzzyMatcher, HybridMatcher


logger = logging.getLogger(__name__)


class IdentityCorrelator:
    """Main orchestration engine for identity correlation
    
    Handles:
    - Loading identities from multiple sources
    - Normalizing identity data
    - Correlating identities using multiple strategies
    - Building unified profiles
    - Maintaining audit trail
    
    Example:
        >>> config = load_config('config/default.yaml')
        >>> correlator = IdentityCorrelator(config)
        >>> identities = correlator.load_from_sources(['workday', 'okta'])
        >>> results = correlator.correlate(identities)
        >>> for profile in results.unified_profiles:
        ...     print(f"{profile.canonical_email}: {profile.confidence_score}%")
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the correlator
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.normalizer = TextNormalizer(config.get("normalization", {}))
        
        # Initialize matchers
        self.exact_matcher = ExactMatcher()
        self.fuzzy_matcher = FuzzyMatcher(
            config.get("matching", {}).get("fuzzy", {})
        )
        self.hybrid_matcher = HybridMatcher(
            self.exact_matcher,
            self.fuzzy_matcher,
            config.get("matching", {}),
        )
        
        # Storage for identities and decisions
        self.identities: List[Identity] = []
        self.matching_decisions: List[MatchingDecision] = []
        self.audit_trail: List[Dict[str, Any]] = []
        
        logger.info(
            f"IdentityCorrelator initialized with config: {config.get('name', 'unnamed')}"
        )
    
    def load_identities(self, identities: List[Identity]) -> None:
        """Load identities into the correlator
        
        Args:
            identities: List of Identity objects
        """
        self.identities.extend(identities)
        logger.info(f"Loaded {len(identities)} identities")
    
    def correlate(self, identities: Optional[List[Identity]] = None) -> CorrelationResult:
        """Correlate identities across sources
        
        Args:
            identities: Optional list of identities to correlate.
                       If None, uses previously loaded identities
        
        Returns:
            CorrelationResult containing unified profiles, metrics, etc.
        """
        start_time = time.time()
        
        if identities:
            self.identities = identities
        
        logger.info(f"Starting correlation of {len(self.identities)} identities")
        
        # Step 1: Normalize identities
        normalized_identities = self._normalize_identities(self.identities)
        
        # Step 2: Perform matching using hybrid approach
        matching_decisions = self._match_identities(normalized_identities)
        
        # Step 3: Build unified profiles
        unified_profiles = self._build_profiles(
            normalized_identities, matching_decisions
        )
        
        # Step 4: Calculate quality metrics
        quality_metrics = self._calculate_metrics(
            unified_profiles, matching_decisions
        )
        
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Find unmatched identities
        matched_ids = set()
        for decision in matching_decisions:
            if decision.matched:
                matched_ids.add(decision.source_identity_id)
                matched_ids.add(decision.target_identity_id)
        
        unmatched = [i for i in normalized_identities if i.id not in matched_ids]
        
        result = CorrelationResult(
            unified_profiles=unified_profiles,
            unmatched_identities=unmatched,
            matching_decisions=matching_decisions,
            quality_metrics=quality_metrics,
            processing_time_ms=processing_time,
        )
        
        logger.info(
            f"Correlation complete: {len(unified_profiles)} profiles, "
            f"{len(unmatched)} unmatched in {processing_time:.1f}ms"
        )
        
        return result
    
    def _normalize_identities(self, identities: List[Identity]) -> List[Identity]:
        """Normalize identity data
        
        Args:
            identities: Raw identities from sources
        
        Returns:
            Normalized identities
        """
        logger.info("Starting normalization phase")
        normalized = []
        
        for identity in identities:
            normalized_copy = Identity(
                source=identity.source,
                source_id=identity.source_id,
                first_name=self.normalizer.normalize(identity.first_name)
                if identity.first_name
                else None,
                last_name=self.normalizer.normalize(identity.last_name)
                if identity.last_name
                else None,
                email=self.normalizer.normalize_email(identity.email)
                if identity.email
                else None,
                phone=self.normalizer.normalize_phone(identity.phone)
                if identity.phone
                else None,
                department=self.normalizer.normalize(identity.department)
                if identity.department
                else None,
                manager_id=identity.manager_id,
                attributes=identity.attributes,
                id=identity.id,
                created_at=identity.created_at,
            )
            normalized.append(normalized_copy)
        
        logger.info(f"Normalized {len(normalized)} identities")
        return normalized
    
    def _match_identities(
        self, identities: List[Identity]
    ) -> List[MatchingDecision]:
        """Match identities across sources
        
        Args:
            identities: Normalized identities
        
        Returns:
            List of matching decisions
        """
        logger.info(f"Starting matching phase with {len(identities)} identities")
        
        decisions: List[MatchingDecision] = []
        processed_pairs = set()
        
        # Compare each pair of identities from different sources
        for i, id1 in enumerate(identities):
            for id2 in identities[i + 1 :]:
                # Skip if same source
                if id1.source == id2.source:
                    continue
                
                # Skip if already processed
                pair_key = tuple(sorted([id1.id, id2.id]))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)
                
                # Run matching
                decision = self._match_pair(id1, id2)
                decisions.append(decision)
        
        logger.info(f"Completed {len(decisions)} pairwise comparisons")
        
        # Log matching statistics
        matched_count = sum(1 for d in decisions if d.matched)
        logger.info(
            f"Matching results: {matched_count} matched, "
            f"{len(decisions) - matched_count} unmatched"
        )
        
        self.matching_decisions.extend(decisions)
        return decisions
    
    def _match_pair(self, id1: Identity, id2: Identity) -> MatchingDecision:
        """Match a pair of identities
        
        Args:
            id1: First identity
            id2: Second identity
        
        Returns:
            MatchingDecision with confidence score
        """
        # Use hybrid matcher
        score, evidence = self.hybrid_matcher.match(id1, id2)
        
        threshold = self.config.get("matching", {}).get("minimum_confidence", 0.85)
        matched = score >= threshold
        
        decision = MatchingDecision(
            source_identity_id=id1.id,
            target_identity_id=id2.id,
            matched=matched,
            confidence_score=score * 100,  # Convert to percentage
            evidence=evidence,
            initiated_by="system.auto_correlator",
        )
        
        return decision
    
    def _build_profiles(
        self,
        identities: List[Identity],
        decisions: List[MatchingDecision],
    ) -> List[UnifiedProfile]:
        """Build unified profiles from matching decisions
        
        Args:
            identities: Normalized identities
            decisions: Matching decisions
        
        Returns:
            List of unified profiles
        """
        logger.info("Starting profile building phase")
        
        # Build adjacency graph from matching decisions
        graph = defaultdict(set)
        for decision in decisions:
            if decision.matched:
                graph[decision.source_identity_id].add(decision.target_identity_id)
                graph[decision.target_identity_id].add(decision.source_identity_id)
        
        # Find connected components (identity clusters)
        visited = set()
        clusters = []
        
        for identity_id in [i.id for i in identities]:
            if identity_id in visited:
                continue
            
            # BFS to find all connected identities
            cluster = set()
            queue = [identity_id]
            
            while queue:
                current_id = queue.pop(0)
                if current_id in visited:
                    continue
                
                visited.add(current_id)
                cluster.add(current_id)
                queue.extend(graph[current_id] - visited)
            
            clusters.append(cluster)
        
        # Build unified profiles from clusters
        profiles = []
        id_map = {i.id: i for i in identities}
        
        for cluster in clusters:
            cluster_identities = [id_map[iid] for iid in cluster if iid in id_map]
            
            if not cluster_identities:
                continue
            
            # Create unified profile
            profile = self._build_profile_from_cluster(
                cluster_identities, decisions
            )
            profiles.append(profile)
        
        logger.info(f"Built {len(profiles)} unified profiles from {len(clusters)} clusters")
        return profiles
    
    def _build_profile_from_cluster(
        self,
        identities: List[Identity],
        decisions: List[MatchingDecision],
    ) -> UnifiedProfile:
        """Build a single unified profile from a cluster of identities
        
        Args:
            identities: List of identities in the cluster
            decisions: All matching decisions
        
        Returns:
            UnifiedProfile
        """
        # Select canonical values (prefer more authoritative sources)
        source_priority = {
            SourceSystem.WORKDAY: 5,
            SourceSystem.ACTIVEDIRECTORY: 4,
            SourceSystem.OKTA: 3,
            SourceSystem.SALESFORCE: 2,
            SourceSystem.SAP: 1,
            SourceSystem.CUSTOM: 0,
        }
        
        # Get best email
        emails = [i.email for i in identities if i.email]
        canonical_email = emails[0] if emails else ""
        
        # Get best names
        first_names = [i.first_name for i in identities if i.first_name]
        last_names = [i.last_name for i in identities if i.last_name]
        
        # Sort by source priority for selection
        sorted_identities = sorted(
            identities, key=lambda i: source_priority.get(i.source, -1), reverse=True
        )
        
        canonical_first = sorted_identities[0].first_name if sorted_identities else None
        canonical_last = sorted_identities[0].last_name if sorted_identities else None
        
        # Build alternate IDs
        alternate_ids = set()
        for identity in identities:
            if identity.email and identity.email != canonical_email:
                alternate_ids.add(identity.email)
            if identity.source_id:
                alternate_ids.add(f"{identity.source.value}:{identity.source_id}")
        
        # Calculate overall confidence
        cluster_decisions = [
            d for d in decisions
            if (d.source_identity_id in [i.id for i in identities]
                and d.target_identity_id in [i.id for i in identities])
        ]
        
        avg_confidence = (
            sum(d.confidence_score for d in cluster_decisions) / len(cluster_decisions)
            if cluster_decisions
            else 95.0
        )
        
        # Build matched sources
        matched_sources = list(set(i.source for i in identities))
        
        # Build source attributes map
        source_attributes = {
            i.source: {
                "first_name": i.first_name,
                "last_name": i.last_name,
                "email": i.email,
                "phone": i.phone,
                "department": i.department,
                **i.attributes,
            }
            for i in identities
        }
        
        profile = UnifiedProfile(
            canonical_email=canonical_email,
            first_name=canonical_first,
            last_name=canonical_last,
            identities=identities,
            confidence_score=avg_confidence,
            matched_sources=matched_sources,
            alternate_ids=list(alternate_ids),
            source_attributes=source_attributes,
            matching_evidence={
                "decisions": len(cluster_decisions),
                "avg_confidence": avg_confidence,
                "sources": [s.value for s in matched_sources],
            },
        )
        
        return profile
    
    def _calculate_metrics(
        self,
        profiles: List[UnifiedProfile],
        decisions: List[MatchingDecision],
    ) -> Dict[str, Any]:
        """Calculate quality metrics
        
        Args:
            profiles: Unified profiles
            decisions: Matching decisions
        
        Returns:
            Dictionary of metrics
        """
        matched_count = sum(1 for d in decisions if d.matched)
        total_comparisons = len(decisions)
        
        if profiles:
            avg_confidence = sum(p.confidence_score for p in profiles) / len(profiles)
            sources_per_profile = [
                len(p.matched_sources) for p in profiles
            ]
            avg_sources = sum(sources_per_profile) / len(profiles)
        else:
            avg_confidence = 0.0
            avg_sources = 0.0
        
        metrics = {
            "total_profiles": len(profiles),
            "matched_count": matched_count,
            "total_comparisons": total_comparisons,
            "match_rate": (
                matched_count / total_comparisons if total_comparisons > 0 else 0
            ),
            "avg_confidence": avg_confidence,
            "avg_sources_per_profile": avg_sources,
            "multi_source_profiles": sum(
                1 for p in profiles if len(p.matched_sources) > 1
            ),
        }
        
        logger.info(f"Quality metrics: {metrics}")
        return metrics
