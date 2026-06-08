"""Basic usage example of Identity Correlation Engine"""

import logging
from identity_engine import (
    IdentityCorrelator,
    Identity,
    SourceSystem,
    load_config,
)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Basic example of identity correlation"""
    
    # Step 1: Load configuration
    logger.info("Loading configuration...")
    config = load_config("config/default.yaml")
    
    # Step 2: Initialize correlator
    logger.info("Initializing Identity Correlator...")
    correlator = IdentityCorrelator(config)
    
    # Step 3: Create sample identities from different sources
    logger.info("Creating sample identities...")
    
    # From Workday (HR system) - source of truth
    workday_identity = Identity(
        source=SourceSystem.WORKDAY,
        source_id="WD-12345",
        first_name="John",
        last_name="Smith",
        email="john.smith@company.com",
        phone="+1-555-0123",
        department="Information Technology",
        attributes={
            "employee_id": "EMP-00123",
            "hire_date": "2020-01-15",
            "status": "Active",
        },
    )
    
    # From Active Directory
    ad_identity = Identity(
        source=SourceSystem.ACTIVEDIRECTORY,
        source_id="CN=jsmith,OU=Users,DC=company,DC=com",
        first_name="john",
        last_name="smith",
        email="jsmith@company.com",
        phone="555-0123",
        department="IT",
        attributes={
            "samAccountName": "jsmith",
            "userPrincipalName": "jsmith@company.com",
        },
    )
    
    # From Okta (SSO platform)
    okta_identity = Identity(
        source=SourceSystem.OKTA,
        source_id="00u1234567890",
        first_name="John",
        last_name="Smith",
        email="john.smith@company.com",
        phone="+1.555.0123",
        department="IT",
        attributes={
            "login": "john.smith@company.com",
            "status": "ACTIVE",
            "provider": True,
        },
    )
    
    # From Salesforce (CRM)
    salesforce_identity = Identity(
        source=SourceSystem.SALESFORCE,
        source_id="005x0000001SGWAA2",
        first_name="John",
        last_name="Smith",
        email="john.smith@company.com",
        phone="(555) 012-3456",
        department="Technology",
        attributes={
            "Title": "Senior Analyst",
            "Email": "john.smith@company.com",
        },
    )
    
    # From SAP (ERP)
    sap_identity = Identity(
        source=SourceSystem.SAP,
        source_id="00012345",
        first_name="Smith",  # Different format!
        last_name="John",    # Last name first!
        email="jsmith@company.sap",
        phone="+15550123",
        department="IT",
        attributes={
            "PERNR": "00012345",
            "STAT": "1",
        },
    )
    
    # Step 4: Load identities into correlator
    logger.info("Loading identities into correlator...")
    identities = [
        workday_identity,
        ad_identity,
        okta_identity,
        salesforce_identity,
        sap_identity,
    ]
    
    correlator.load_identities(identities)
    
    # Step 5: Perform correlation
    logger.info("Correlating identities across sources...")
    results = correlator.correlate()
    
    # Step 6: Display results
    logger.info("\n" + "=" * 80)
    logger.info("CORRELATION RESULTS")
    logger.info("=" * 80)
    
    logger.info(f"\nTotal Unified Profiles: {len(results.unified_profiles)}")
    logger.info(f"Total Unmatched Identities: {len(results.unmatched_identities)}")
    logger.info(f"Processing Time: {results.processing_time_ms:.1f}ms")
    
    # Display unified profiles
    logger.info("\n" + "-" * 80)
    logger.info("UNIFIED PROFILES")
    logger.info("-" * 80)
    
    for i, profile in enumerate(results.unified_profiles, 1):
        logger.info(f"\nProfile #{i}:")
        logger.info(f"  Canonical Email: {profile.canonical_email}")
        logger.info(f"  Name: {profile.first_name} {profile.last_name}")
        logger.info(f"  Confidence Score: {profile.confidence_score:.1f}%")
        logger.info(f"  Matched Sources: {', '.join(s.value for s in profile.matched_sources)}")
        logger.info(f"  Alternate IDs: {', '.join(profile.alternate_ids)}")
        logger.info(f"  Department: {profile.department}")
        logger.info(f"  Phone: {profile.phone}")
    
    # Display quality metrics
    logger.info("\n" + "-" * 80)
    logger.info("QUALITY METRICS")
    logger.info("-" * 80)
    
    for key, value in results.quality_metrics.items():
        if isinstance(value, float):
            logger.info(f"  {key}: {value:.2%}" if value <= 1.0 else f"  {key}: {value}")
        else:
            logger.info(f"  {key}: {value}")
    
    # Display unmatched identities (if any)
    if results.unmatched_identities:
        logger.info("\n" + "-" * 80)
        logger.info("UNMATCHED IDENTITIES")
        logger.info("-" * 80)
        
        for identity in results.unmatched_identities:
            logger.info(
                f"\n  Source: {identity.source.value} | "
                f"Email: {identity.email} | "
                f"Name: {identity.first_name} {identity.last_name}"
            )
    
    # Display matching decisions
    logger.info("\n" + "-" * 80)
    logger.info("MATCHING DECISIONS (Top 5)")
    logger.info("-" * 80)
    
    for decision in results.matching_decisions[:5]:
        status = "✓ MATCHED" if decision.matched else "✗ NOT MATCHED"
        logger.info(
            f"\n  {status} | Confidence: {decision.confidence_score:.1f}% | "
            f"Source {decision.source_identity_id[:8]}... → "
            f"Target {decision.target_identity_id[:8]}..."
        )
        
        if decision.evidence:
            for evidence in decision.evidence:
                logger.info(f"    - {evidence.strategy.value}: {evidence.score:.2%}")


if __name__ == "__main__":
    main()
