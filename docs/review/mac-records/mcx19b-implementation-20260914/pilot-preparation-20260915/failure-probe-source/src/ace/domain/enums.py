from enum import Enum


class ControlRating(str, Enum):
    """Board-facing rating assigned to an assurance control."""

    ADEQUATE = "ADEQUATE"
    PARTIALLY_ADEQUATE = "PARTIALLY_ADEQUATE"
    INADEQUATE = "INADEQUATE"


class HazardCategory(str, Enum):
    """WHS hazard and governance categories supported by ACE."""

    BESS_THERMAL_RUNAWAY = "BESS_THERMAL_RUNAWAY"
    HV_ENERGIZATION = "HV_ENERGIZATION"
    ARC_FLASH = "ARC_FLASH"
    SIMOPS = "SIMOPS"
    SOCI_CYBER_PHYSICAL = "SOCI_CYBER_PHYSICAL"
    TPRM_CONTRACTOR_ONBOARDING = "TPRM_CONTRACTOR_ONBOARDING"
    GOVERNANCE_OVERSIGHT = "GOVERNANCE_OVERSIGHT"
    SAFETY_IN_DESIGN = "SAFETY_IN_DESIGN"
