"""Tests for Identity Correlation Engine"""

import pytest
from identity_engine import (
    IdentityCorrelator,
    Identity,
    SourceSystem,
    MatchingStrategy,
    load_config,
)
from identity_engine.normalizers import TextNormalizer, extract_initials
from identity_engine.matchers import ExactMatcher, FuzzyMatcher, HybridMatcher


class TestNormalization:
    """Test data normalization"""
    
    def test_normalize_removes_diacritics(self):
        """Test diacritical mark removal"""
        normalizer = TextNormalizer({"remove_diacritics": True})
        assert normalizer.normalize("José") == "jose"
        assert normalizer.normalize("Müller") == "muller"
        assert normalizer.normalize("Björn") == "bjorn"
    
    def test_normalize_case(self):
        """Test case normalization"""
        normalizer = TextNormalizer({"case_sensitive": False})
        assert normalizer.normalize("JohnSmith") == "johnsmith"
        assert normalizer.normalize("JOHN SMITH") == "john smith"
    
    def test_normalize_email(self):
        """Test email normalization"""
        normalizer = TextNormalizer({})
        assert normalizer.normalize_email("John.Smith@COMPANY.COM") == "johnsmith@company.com"
        assert normalizer.normalize_email("j_smith@company.com") == "jsmith@company.com"
    
    def test_normalize_phone(self):
        """Test phone normalization"""
        normalizer = TextNormalizer({})
        assert normalizer.normalize_phone("555-0123").endswith("5550123")
        assert normalizer.normalize_phone("(555) 012-3456").endswith("5550123456")


class TestMatching:
    """Test identity matching algorithms"""
    
    @pytest.fixture
    def sample_identities(self):
        """Create sample identities for testing"""
        id1 = Identity(
            source=SourceSystem.WORKDAY,
            source_id="WD-123",
            first_name="john",
            last_name="smith",
            email="john.smith@company.com",
        )
        
        id2 = Identity(
            source=SourceSystem.ACTIVEDIRECTORY,
            source_id="AD-456",
            first_name="john",
            last_name="smith",
            email="jsmith@company.com",
        )
        
        id3 = Identity(
            source=SourceSystem.OKTA,
            source_id="OK-789",
            first_name="jon",  # Typo
            last_name="smyth",  # Alternative spelling
            email="jon.smyth@company.com",
        )
        
        return id1, id2, id3
    
    def test_exact_matcher_perfect_match(self, sample_identities):
        """Test exact matching with identical fields"""
        matcher = ExactMatcher()
        id1, id2, _ = sample_identities
        
        # Modify id1 to have exact same fields as id2
        id1.email = id2.email
        
        score, evidence = matcher.match(id1, id2)
        assert score >= 0.5  # Should match on name at least
    
    def test_fuzzy_matcher_typos(self, sample_identities):
        """Test fuzzy matching handles typos"""
        matcher = FuzzyMatcher({"threshold": 0.85})
        _, _, id3 = sample_identities
        id2 = sample_identities[1]
        
        score, evidence = matcher.match(id2, id3)
        assert score > 0.7  # Should catch the similarity despite typos
    
    def test_hybrid_matcher_combines_scores(self, sample_identities):
        """Test hybrid matcher combines multiple strategies"""
        config = {
            "strategies": [
                {"name": "exact_match", "weight": 0.4},
                {"name": "fuzzy_match", "weight": 0.3},
                {"name": "composite_match", "weight": 0.2},
            ],
            "fuzzy": {"threshold": 0.85},
            "field_weights": {
                "email": 0.4,
                "first_name": 0.3,
                "last_name": 0.3,
            },
        }
        
        exact = ExactMatcher()
        fuzzy = FuzzyMatcher(config["fuzzy"])
        hybrid = HybridMatcher(exact, fuzzy, config)
        
        id1, id2, _ = sample_identities
        score, evidence = hybrid.match(id1, id2)
        
        assert 0.0 <= score <= 1.0
        assert len(evidence) > 0


class TestCorrelation:
    """Test identity correlation process"""
    
    def test_correlate_single_identity(self):
        """Test correlation with single identity"""
        config = load_config()
        correlator = IdentityCorrelator(config)
        
        identity = Identity(
            source=SourceSystem.WORKDAY,
            source_id="WD-123",
            first_name="john",
            last_name="smith",
            email="john.smith@company.com",
        )
        
        results = correlator.correlate([identity])
        
        assert len(results.unified_profiles) == 1
        assert len(results.unmatched_identities) == 0
    
    def test_correlate_multiple_sources(self):
        """Test correlation with multiple sources"""
        config = load_config()
        correlator = IdentityCorrelator(config)
        
        identities = [
            Identity(
                source=SourceSystem.WORKDAY,
                source_id="WD-123",
                first_name="john",
                last_name="smith",
                email="john.smith@company.com",
            ),
            Identity(
                source=SourceSystem.ACTIVEDIRECTORY,
                source_id="AD-456",
                first_name="john",
                last_name="smith",
                email="jsmith@company.com",
            ),
            Identity(
                source=SourceSystem.OKTA,
                source_id="OK-789",
                first_name="john",
                last_name="smith",
                email="john.smith@company.com",
            ),
        ]
        
        results = correlator.correlate(identities)
        
        # Should correlate to 1 profile (with possible typos/variations handled)
        assert len(results.unified_profiles) >= 1
        assert len(results.matching_decisions) > 0
    
    def test_quality_metrics_calculated(self):
        """Test quality metrics are calculated"""
        config = load_config()
        correlator = IdentityCorrelator(config)
        
        identities = [
            Identity(
                source=SourceSystem.WORKDAY,
                source_id="WD-123",
                first_name="john",
                last_name="smith",
                email="john.smith@company.com",
            ),
            Identity(
                source=SourceSystem.ACTIVEDIRECTORY,
                source_id="AD-456",
                first_name="john",
                last_name="smith",
                email="john.smith@company.com",
            ),
        ]
        
        results = correlator.correlate(identities)
        
        assert "total_profiles" in results.quality_metrics
        assert "match_rate" in results.quality_metrics
        assert "avg_confidence" in results.quality_metrics


class TestConfiguration:
    """Test configuration management"""
    
    def test_load_default_config(self):
        """Test default configuration loads"""
        config = load_config()
        
        assert "matching" in config
        assert "normalization" in config
        assert "storage" in config
    
    def test_config_has_required_keys(self):
        """Test configuration has all required keys"""
        config = load_config()
        
        required = ["matching", "normalization", "sources"]
        for key in required:
            assert key in config, f"Missing required config key: {key}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
