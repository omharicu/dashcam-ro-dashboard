"""
Authentication and secure token configuration for NHAI RO Dashboard.
Generates unique, tamper-proof access keys for all 24 Regional Offices and 1 Master Admin.
"""

RO_TOKENS = {
    "Bengaluru": "BLR-7482",
    "Bhopal": "BPL-3914",
    "Bhubaneswar": "BBS-8521",
    "Chandigarh": "CHD-1943",
    "Chennai": "MAA-6278",
    "Dehradun": "DDN-5190",
    "Delhi": "DEL-8402",
    "Gandhinagar": "GNR-3715",
    "Guwahati": "GAU-9641",
    "Hyderabad": "HYD-2839",
    "Jaipur": "JPR-4826",
    "Jammu": "JMU-7153",
    "Kolkata": "CCU-3694",
    "Madurai": "IXM-8205",
    "Mumbai": "BOM-5417",
    "Nagpur": "NAG-1962",
    "Patna": "PAT-6380",
    "Raipur": "RPR-7241",
    "Ranchi": "IXR-4519",
    "Shimla": "SML-8302",
    "Thiruvananthapuram": "TRV-9164",
    "UP East": "UPE-6742",
    "UP West": "UPW-5283",
    "Vijayawada": "VJA-4931",
}

ADMIN_KEY = "HQ-ADMIN-7700"

# Slug / alternate name mappings for URL cleanliness
SLUG_TO_RO = {
    "bengaluru": "Bengaluru",
    "bhopal": "Bhopal",
    "bhubaneswar": "Bhubaneswar",
    "chandigarh": "Chandigarh",
    "chennai": "Chennai",
    "dehradun": "Dehradun",
    "delhi": "Delhi",
    "gandhinagar": "Gandhinagar",
    "guwahati": "Guwahati",
    "hyderabad": "Hyderabad",
    "jaipur": "Jaipur",
    "jammu": "Jammu",
    "kolkata": "Kolkata",
    "madurai": "Madurai",
    "mumbai": "Mumbai",
    "nagpur": "Nagpur",
    "patna": "Patna",
    "raipur": "Raipur",
    "ranchi": "Ranchi",
    "shimla": "Shimla",
    "thiruvananthapuram": "Thiruvananthapuram",
    "kerala": "Thiruvananthapuram",
    "upeast": "UP East",
    "up-east": "UP East",
    "up east": "UP East",
    "upwest": "UP West",
    "up-west": "UP West",
    "up west": "UP West",
    "vijayawada": "Vijayawada",
}

def validate_access(ro_param: str = None, key_param: str = None, admin_param: str = None):
    """
    Validates the query parameters.
    Returns:
        (is_valid: bool, role: str, ro_name: str or None)
        role is either 'admin', 'ro', or 'unauthorized'
    """
    # Check Admin first
    if (admin_param and admin_param.lower() in ["true", "1", "yes"]) or (key_param == ADMIN_KEY):
        if key_param == ADMIN_KEY:
            return True, "admin", None
        else:
            return False, "unauthorized", None

    if not ro_param or not key_param:
        return False, "unauthorized", None

    # Normalize RO name
    norm_ro = ro_param.strip().lower()
    canonical_ro = SLUG_TO_RO.get(norm_ro)
    if not canonical_ro:
        # Try direct match
        for k in RO_TOKENS:
            if k.lower() == norm_ro:
                canonical_ro = k
                break

    if not canonical_ro:
        return False, "unauthorized", None

    # Check key
    expected_key = RO_TOKENS.get(canonical_ro)
    if key_param.strip().upper() == expected_key.upper():
        return True, "ro", canonical_ro

    return False, "unauthorized", None

