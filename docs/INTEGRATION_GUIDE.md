# Integration Guide

## Overview

This guide explains how to integrate Identity Correlation Engine with different source systems and build custom extractors.

## Supported Systems (Out-of-box)

| System | Type | Status |
|--------|------|--------|
| **Workday** | HR System | ✅ Implemented |
| **Active Directory** | Directory | ✅ Implemented |
| **Okta** | SSO Platform | ✅ Implemented |
| **Salesforce** | CRM | ✅ Implemented |
| **SAP** | ERP | ✅ Implemented |
| **Custom Systems** | Any | ✅ Plugin Pattern |

## Building a Custom Extractor

### Step 1: Extend BaseExtractor

```python
from identity_engine.extractors import BaseExtractor
from identity_engine import Identity, SourceSystem
from typing import List

class MyCustomSystemExtractor(BaseExtractor):
    """Extractor for MyCustomSystem"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url")
    
    def fetch_identities(self) -> List[Identity]:
        """Fetch all identities from the system"""
        identities = []
        
        # Call your API to get users
        response = requests.get(
            f"{self.base_url}/api/v1/users",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        for user in response.json():
            identity = Identity(
                source=SourceSystem.CUSTOM,
                source_id=user["id"],
                first_name=user.get("firstName"),
                last_name=user.get("lastName"),
                email=user.get("email"),
                phone=user.get("phone"),
                department=user.get("department"),
                attributes={
                    "status": user.get("status"),
                    "custom_field": user.get("customField"),
                }
            )
            identities.append(identity)
        
        return identities
    
    def validate_connection(self) -> bool:
        """Test connection to the system"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/health",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def supports_incremental_sync(self) -> bool:
        """Return True if system supports delta sync"""
        return True
    
    def fetch_identities_since(self, timestamp: datetime) -> List[Identity]:
        """Fetch only identities modified since timestamp"""
        identities = []
        
        response = requests.get(
            f"{self.base_url}/api/v1/users?modifiedSince={timestamp.isoformat()}",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        for user in response.json():
            # Similar processing as fetch_identities()
            pass
        
        return identities
```

### Step 2: Register Extractor

```yaml
# config/default.yaml

sources:
  my_custom_system:
    enabled: true
    connector_type: "rest_api"
    connector_class: "MyCustomSystemExtractor"
    base_url: "${CUSTOM_SYSTEM_URL}"
    api_key: "${CUSTOM_SYSTEM_API_KEY}"
```

### Step 3: Use in Correlator

```python
from identity_engine import IdentityCorrelator, load_config
from my_extractors import MyCustomSystemExtractor

# Extractors are auto-loaded based on config
config = load_config("config/default.yaml")
correlator = IdentityCorrelator(config)

# Load identities from all configured sources
workday_identities = # ... fetch from Workday extractor
custom_identities = MyCustomSystemExtractor(config["sources"]["my_custom_system"]).fetch_identities()

correlator.load_identities(workday_identities + custom_identities)
results = correlator.correlate()
```

## API Integration Patterns

### REST API Pattern

```python
import requests
from datetime import datetime, timedelta

class RESTExtractor(BaseExtractor):
    """Generic REST API extractor"""
    
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("base_url")
        self.headers = {
            "Authorization": f"Bearer {config.get('api_token')}",
            "Content-Type": "application/json"
        }
        self.page_size = config.get("page_size", 100)
    
    def fetch_identities(self) -> List[Identity]:
        identities = []
        page = 1
        
        while True:
            # Paginated request
            response = requests.get(
                f"{self.base_url}/users?page={page}&pageSize={self.page_size}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                break
            
            data = response.json()
            if not data.get("items"):
                break
            
            for item in data["items"]:
                identities.append(self._map_to_identity(item))
            
            page += 1
        
        return identities
    
    def _map_to_identity(self, raw_data: dict) -> Identity:
        """Map API response to Identity model"""
        return Identity(
            source=SourceSystem.CUSTOM,
            source_id=raw_data["id"],
            first_name=raw_data.get("firstName"),
            last_name=raw_data.get("lastName"),
            email=raw_data.get("email"),
            phone=raw_data.get("phone"),
            department=raw_data.get("department"),
        )
```

### LDAP Pattern

```python
import ldap

class LDAPExtractor(BaseExtractor):
    """LDAP directory extractor"""
    
    def __init__(self, config: Dict[str, Any]):
        self.server_url = f"ldap://{config['server']}:{config.get('port', 389)}"
        self.search_base = config.get("search_base", "DC=company,DC=com")
        self.bind_dn = config.get("bind_dn")
        self.bind_password = config.get("bind_password")
    
    def fetch_identities(self) -> List[Identity]:
        ldap_conn = ldap.initialize(self.server_url)
        ldap_conn.simple_bind_s(self.bind_dn, self.bind_password)
        
        identities = []
        
        # Search for all users
        search_filter = "(&(objectClass=person)(mail=*))"
        attributes = ["cn", "givenName", "sn", "mail", "telephoneNumber", "department"]
        
        results = ldap_conn.search_s(self.search_base, ldap.SCOPE_SUBTREE, search_filter, attributes)
        
        for dn, attrs in results:
            if dn is None:  # Skip search references
                continue
            
            identity = Identity(
                source=SourceSystem.ACTIVEDIRECTORY,
                source_id=dn,
                first_name=self._get_ldap_attr(attrs, "givenName"),
                last_name=self._get_ldap_attr(attrs, "sn"),
                email=self._get_ldap_attr(attrs, "mail"),
                phone=self._get_ldap_attr(attrs, "telephoneNumber"),
                department=self._get_ldap_attr(attrs, "department"),
            )
            identities.append(identity)
        
        ldap_conn.unbind_s()
        return identities
    
    @staticmethod
    def _get_ldap_attr(attrs: dict, key: str) -> str:
        """Safely extract LDAP attribute"""
        value = attrs.get(key, [None])
        if value and value[0]:
            return value[0].decode() if isinstance(value[0], bytes) else value[0]
        return None
```

### OData Pattern (SAP, Dynamics)

```python
import requests
from odata import OData

class ODataExtractor(BaseExtractor):
    """OData API extractor for SAP, Dynamics, etc."""
    
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("base_url")
        self.username = config.get("username")
        self.password = config.get("password")
        self.client = OData(
            url=self.base_url,
            username=self.username,
            password=self.password
        )
    
    def fetch_identities(self) -> List[Identity]:
        # Query: /service/Employees?$filter=Status eq 'Active'
        request = self.client.build_request("Employees", {
            "$filter": "Status eq 'Active'",
            "$select": "ID,FirstName,LastName,Email,Phone,Department"
        })
        
        identities = []
        for record in request:
            identity = Identity(
                source=SourceSystem.SAP,
                source_id=record["ID"],
                first_name=record.get("FirstName"),
                last_name=record.get("LastName"),
                email=record.get("Email"),
                phone=record.get("Phone"),
                department=record.get("Department"),
            )
            identities.append(identity)
        
        return identities
```

## Data Mapping Strategies

### Strategy 1: Direct Field Mapping

```python
mapping = {
    "id": "source_id",
    "firstName": "first_name",
    "lastName": "last_name",
    "primaryEmail": "email",
    "workPhone": "phone",
}

def map_fields(raw_data: dict, mapping: dict) -> Identity:
    mapped = {}
    for raw_key, identity_key in mapping.items():
        if raw_key in raw_data:
            mapped[identity_key] = raw_data[raw_key]
    
    return Identity(source=SourceSystem.CUSTOM, **mapped)
```

### Strategy 2: Transform Functions

```python
def extract_name_parts(full_name: str) -> Tuple[str, str]:
    """Extract first and last name from full name"""
    parts = full_name.split()
    first = parts[0] if len(parts) > 0 else ""
    last = " ".join(parts[1:]) if len(parts) > 1 else ""
    return first, last

def map_with_transforms(raw_data: dict) -> Identity:
    first, last = extract_name_parts(raw_data["name"])
    
    return Identity(
        source=SourceSystem.CUSTOM,
        source_id=raw_data["id"],
        first_name=first,
        last_name=last,
        email=raw_data["email"].lower(),
        phone=normalize_phone(raw_data.get("phone")),
    )
```

## Incremental Sync

```python
class IncrementalExtractor(BaseExtractor):
    """Base class for incremental sync support"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.last_sync_file = config.get("last_sync_file", ".last_sync")
    
    def fetch_identities(self) -> List[Identity]:
        """Full sync"""
        return self._fetch_from_source()
    
    def fetch_incremental(self) -> List[Identity]:
        """Incremental sync since last run"""
        last_sync = self._read_last_sync()
        identities = self.fetch_identities_since(last_sync)
        self._write_last_sync(datetime.now())
        return identities
    
    def fetch_identities_since(self, timestamp: datetime) -> List[Identity]:
        """Override to implement delta query"""
        raise NotImplementedError
    
    def _read_last_sync(self) -> datetime:
        if os.path.exists(self.last_sync_file):
            with open(self.last_sync_file) as f:
                return datetime.fromisoformat(f.read())
        return datetime.min
    
    def _write_last_sync(self, timestamp: datetime):
        with open(self.last_sync_file, "w") as f:
            f.write(timestamp.isoformat())
```

## Error Handling and Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class RobustExtractor(BaseExtractor):
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def fetch_identities(self) -> List[Identity]:
        """Automatically retry on failure"""
        try:
            response = requests.get(
                f"{self.base_url}/users",
                timeout=30
            )
            response.raise_for_status()
            return self._parse_response(response)
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
```

## Testing Your Extractor

```python
def test_custom_extractor():
    config = {
        "base_url": "http://localhost:8080",
        "api_key": "test-key"
    }
    
    extractor = MyCustomSystemExtractor(config)
    
    # Test connection
    assert extractor.validate_connection()
    
    # Test fetch
    identities = extractor.fetch_identities()
    assert len(identities) > 0
    assert all(isinstance(i, Identity) for i in identities)
    
    # Verify mapping
    identity = identities[0]
    assert identity.source == SourceSystem.CUSTOM
    assert identity.email is not None
```

## Best Practices

1. **Error Handling**: Always handle API errors gracefully
2. **Logging**: Log important events and errors
3. **Timeouts**: Set reasonable timeouts (30s recommended)
4. **Pagination**: Handle paginated responses
5. **Rate Limiting**: Respect API rate limits
6. **Credentials**: Never hardcode credentials, use environment variables
7. **Testing**: Test with mock data before deploying
8. **Validation**: Validate data before returning

## Troubleshooting

### Issue: "Connection refused"
- Check service URL is correct
- Verify network connectivity
- Check firewall rules

### Issue: "Authentication failed"
- Verify credentials in config
- Check token expiration
- Verify scopes/permissions

### Issue: "Identities missing fields"
- Check field names match source system
- Verify user permissions allow field access
- Check API documentation for field availability

---

For more examples, see `examples/` directory.
