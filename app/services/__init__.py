"""Patient Explorer V1.0 Services.

This module contains business logic services for:
- Patient data consolidation (Excel + Spruce → JSON)
- Azure blob storage sync
- Patient matching
"""

from .patient_consolidator import PatientConsolidator

__all__ = ["PatientConsolidator"]
