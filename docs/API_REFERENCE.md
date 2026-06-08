# API Reference

## Core Classes

### `IdentityCorrelator`

Main orchestration engine for identity correlation.

#### Constructor

```python
def __init__(self, config: Dict[str, Any]) -> None:
    """
    Initialize the correlator
    
    Args:
        config: Configuration dictionary with:
            - matching: Matching strategy configuration
            - normalization: Normalization settings
            - storage: Storage backend configuration
    """
```

#### Methods

##### `load_identities()`

```python
def load_identities(self, identities: List[Identity]) -> None:
    """
    Load identities into the correlator
    
    Args:
        identities: List of Identity objects from different sources
    """
```

**Example:**
```python
identities = [
    Identity(source=SourceSystem.WORKDAY, ...),
    Identity(source=SourceSystem.OKTA, ...),
]
correlator.load_identities(identities)
```

##### `correlate()`

```python
def correlate(self, identities: Optional[List[Identity]] = None) -> CorrelationResult:
    """
    Correlate identities across sources
    
    Args:
        identities: Optional list of identities to correlate.
                   If None, uses previously loaded identities
    
    Returns:
        CorrelationResult with:
            - unified_profiles: List of merged profiles
            - unmatched_identities: Identities that couldn't be correlated
            - matching_decisions: Audit trail of matches
            - quality_metrics: Statistics about correlation
            - processing_time_ms: Execution time
    
    Raises:
        ValueError: If no identities loaded
    """
```

**Example:**
```python
results = correlator.correlate()

for profile in results.unified_profiles:
    print(f"Email: {profile.canonical_email}")
    print(f"Confidence: {profile.confidence_score}%")
    print(f"Sources: {profile.matched_sources}")
```

---

## Data Models

### `Identity`

Represents an identity from a source system.

```python
@dataclass
class Identity:
    source: SourceSystem              # Source system enum
    source_id: str                    # Unique ID in source
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    manager_id: Optional[str] = None
    attributes: Dict[str, Any] = {}  # Custom attributes
    
    # Metadata
    id: str                           # UUID for this identity
    created_at: datetime              # When loaded
```

**Example:**
```python
from identity_engine import Identity, SourceSystem

identity = Identity(
    source=SourceSystem.WORKDAY,
    source_id="WD-12345",
    first_name="John",
    last_name="Smith",
    email="john.smith@company.com",
    department="IT",
    attributes={
        "employee_id": "EMP-00123",
        "hire_date": "2020-01-15",
    }
)
```

### `UnifiedProfile`

Unified identity profile combining data from multiple sources.

```python
@dataclass
class UnifiedProfile:
    id: str                                        # Profile UUID
    canonical_email: str                          # Primary email
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    
    identities: List[Identity] = []               # Correlated identities
    confidence_score: float = 0.0                 # 0-100%
    matched_sources: List[SourceSystem] = []      # Systems included
    alternate_ids: List[str] = []                 # Alternative identifiers
    
    source_attributes: Dict[SourceSystem, Dict] = {}  # Attributes per source
    matching_evidence: Dict[str, Any] = {}        # How match was made
    audit_trail: List[MatchingDecision] = []      # Matching decisions
    
    created_at: datetime = None
    updated_at: datetime = None
```

**Properties:**
```python
profile.canonical_email      # john.smith@company.com
profile.confidence_score     # 96.2 (percentage)
profile.matched_sources      # [WORKDAY, ACTIVEDIRECTORY, OKTA]
profile.alternate_ids        # ['jsmith', 'j.smith', 'smithj']
```

### `MatchingDecision`

Audit trail record of a matching decision.

```python
@dataclass
class MatchingDecision:
    id: str                                # Decision UUID
    source_identity_id: str                # First identity ID
    target_identity_id: str                # Second identity ID
    matched: bool                          # Match yes/no
    confidence_score: float                # 0-100%
    evidence: List[MatchingEvidence]       # Why decision made
    initiated_by: str                      # Who initiated
    timestamp: datetime                    # When decided
    source_quality_factor: float = 1.0
    historical_accuracy_factor: float = 1.0
```

### `CorrelationResult`

Result of the correlation process.

```python
@dataclass
class CorrelationResult:
    unified_profiles: List[UnifiedProfile]     # Merged profiles
    unmatched_identities: List[Identity]       # Couldn't match
    matching_decisions: List[MatchingDecision] # Audit trail
    quality_metrics: Dict[str, Any]            # Statistics
    processing_time_ms: float                  # Execution time
```

**Metrics included:**
- `total_profiles`: Number of unified profiles
- `matched_count`: Number of successful matches
- `match_rate`: Percentage of identities matched
- `avg_confidence`: Average confidence score
- `avg_sources_per_profile`: Average sources per profile
- `multi_source_profiles`: Count of profiles with 2+ sources

---

## Enums

### `SourceSystem`

```python
class SourceSystem(Enum):
    WORKDAY = "workday"
    ACTIVEDIRECTORY = "activedirectory"
    OKTA = "okta"
    SALESFORCE = "salesforce"
    SAP = "sap"
    CUSTOM = "custom"
```

### `MatchingStrategy`

```python
class MatchingStrategy(Enum):
    EXACT = "exact_match"
    FUZZY = "fuzzy_match"
    COMPOSITE = "composite_match"
    ML_BASED = "ml_match"
    HYBRID = "hybrid"
```

---

## Configuration

### `load_config()`

```python
def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file or environment
    
    Args:
        config_path: Path to YAML config file
    
    Returns:
        Configuration dictionary
    """
```

**Configuration Keys:**

```yaml
identity_engine:
  name: "Identity Correlation Engine"
  version: "1.0.0"

matching:
  minimum_confidence: 0.85  # 85% confidence threshold
  strategies:
    - name: "exact_match"
      weight: 0.4
      threshold: 0.95
    - name: "fuzzy_match"
      weight: 0.3
      threshold: 0.85

normalization:
  case_sensitive: false         # Normalize case
  remove_diacritics: true       # José → Jose
  standardize_spacing: true     # Remove extra spaces
  remove_punctuation: false     # Keep punctuation

storage:
  backend: "postgresql"         # in_memory, postgresql, elasticsearch
  connection_string: "postgresql://..."

audit:
  enabled: true
  immutable_log: true           # Prevent tampering
```

---

## Utility Functions

### Normalizers

```python
from identity_engine.normalizers import TextNormalizer

normalizer = TextNormalizer(config={"remove_diacritics": True})

# Normalize text
result = normalizer.normalize("José Smith")  # "jose smith"

# Normalize email
email = normalizer.normalize_email("John.Smith@COMPANY.COM")  # "johnsmith@company.com"

# Normalize phone
phone = normalizer.normalize_phone("(555) 012-3456")  # "+15550123456"

# Phonetic variation
phonetic = normalizer.get_phonetic_variation("Smith")  # "SM0" (Soundex)
```

### Matchers

```python
from identity_engine.matchers import ExactMatcher, FuzzyMatcher

# Exact matcher
matcher = ExactMatcher()
score, evidence = matcher.match(identity1, identity2)

# Fuzzy matcher with Levenshtein distance
fuzzy = FuzzyMatcher({"threshold": 0.85})
score, evidence = fuzzy.match(identity1, identity2)
```

---

## Complete Example

```python
from identity_engine import (
    IdentityCorrelator,
    Identity,
    SourceSystem,
    load_config,
)

# 1. Load configuration
config = load_config("config/default.yaml")

# 2. Initialize correlator
correlator = IdentityCorrelator(config)

# 3. Create identities
workday = Identity(
    source=SourceSystem.WORKDAY,
    source_id="WD-123",
    first_name="John",
    last_name="Smith",
    email="john.smith@company.com",
)

okta = Identity(
    source=SourceSystem.OKTA,
    source_id="OK-789",
    first_name="John",
    last_name="Smith",
    email="john.smith@company.com",
)

# 4. Correlate
results = correlator.correlate([workday, okta])

# 5. Process results
for profile in results.unified_profiles:
    print(f"Email: {profile.canonical_email}")
    print(f"Confidence: {profile.confidence_score}%")
    print(f"Sources: {[s.value for s in profile.matched_sources]}")
    
    # Access audit trail
    for decision in profile.audit_trail:
        print(f"  Decision: {decision.matched} ({decision.confidence_score}%)")

print(f"\nMetrics: {results.quality_metrics}")
print(f"Processing time: {results.processing_time_ms}ms")
```

---

## Error Handling

```python
from identity_engine import IdentityCorrelator
from identity_engine.config import validate_config

try:
    config = load_config("config/default.yaml")
    validate_config(config)
    
    correlator = IdentityCorrelator(config)
    results = correlator.correlate()
    
except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"Correlation error: {e}")
```

---

## Performance Considerations

### Benchmarks
- **Matching Time**: ~0.5ms per identity pair
- **Memory**: ~2GB for 100K identities
- **Throughput**: 50K identities/minute (batch mode)

### Optimization Tips
1. **Batch Processing**: Process identities in batches
2. **Indexing**: Use database indexes on email, source_id
3. **Caching**: Cache normalized values
4. **Parallel Matching**: Use multiple workers for independent comparisons

---

## Versioning

This API follows semantic versioning:
- **MAJOR**: Breaking API changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

Current version: `1.0.0`
