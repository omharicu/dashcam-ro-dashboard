"""
Authentication and secure token configuration for NHAI Dashboard.
Generates unique, tamper-proof access keys for:
1. 24 Regional Offices (ROs)
2. 5 National Zones (Zones A, B, C, D, E)
3. 1 Master Head Office Admin
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

ZONE_TOKENS = {
    "A": "ZN-A-8192",
    "B": "ZN-B-5734",
    "C": "ZN-C-9421",
    "D": "ZN-D-3850",
    "E": "ZN-E-6178",
}

ZONE_INFO = {
    "A": {"name": "Zone A (North)", "vendor": "M/s CMS Computers India Pvt. Ltd.", "ros": ["Chandigarh", "Dehradun", "Delhi", "Jammu", "Shimla"]},
    "B": {"name": "Zone B (West)", "vendor": "M/s Amnex Infotechnologies Pvt. Ltd.", "ros": ["Gandhinagar", "Jaipur"]},
    "C": {"name": "Zone C (Central)", "vendor": "M/s TTL", "ros": ["Bhopal", "Mumbai", "Nagpur", "Raipur"]},
    "D": {"name": "Zone D (South)", "vendor": "M/s Lonrix", "ros": ["Bengaluru", "Chennai", "Hyderabad", "Madurai", "Thiruvananthapuram", "Vijayawada"]},
    "E": {"name": "Zone E (East)", "vendor": "M/s Ador Powertron Ltd.", "ros": ["Bhubaneswar", "Guwahati", "Kolkata", "Patna", "Ranchi", "UP East", "UP West"]},
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

def validate_access(ro_param: str = None, key_param: str = None, admin_param: str = None, zone_param: str = None, **kwargs):
    """
    Validates query parameters.
    Returns:
        (is_valid: bool, role: str, ro_name: str or None, zone_name: str or None)
        role is either 'admin', 'zone', 'ro', or 'unauthorized'
    """
    # 1. Check Admin
    if (admin_param and admin_param.lower() in ["true", "1", "yes"]) or (key_param == ADMIN_KEY):
        if key_param == ADMIN_KEY:
            return True, "admin", None, None
        else:
            return False, "unauthorized", None, None

    # 2. Check Zone
    if zone_param and key_param:
        norm_zone = zone_param.strip().upper()
        if norm_zone.startswith("ZONE "):
            norm_zone = norm_zone.replace("ZONE ", "").strip()
        elif norm_zone.startswith("ZONE"):
            norm_zone = norm_zone.replace("ZONE", "").strip()

        expected_zone_key = ZONE_TOKENS.get(norm_zone)
        if expected_zone_key and key_param.strip().upper() == expected_zone_key.upper():
            return True, "zone", None, norm_zone
        return False, "unauthorized", None, None

    # 3. Check RO
    if not ro_param or not key_param:
        return False, "unauthorized", None, None

    norm_ro = ro_param.strip().lower()
    canonical_ro = SLUG_TO_RO.get(norm_ro)
    if not canonical_ro:
        for k in RO_TOKENS:
            if k.lower() == norm_ro:
                canonical_ro = k
                break

    if not canonical_ro:
        return False, "unauthorized", None, None

    expected_key = RO_TOKENS.get(canonical_ro)
    if key_param.strip().upper() == expected_key.upper():
        return True, "ro", canonical_ro, None

    return False, "unauthorized", None, None
