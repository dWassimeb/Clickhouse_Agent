"""
Database metadata and schema definitions for the ClickHouse Agent.
"""

from typing import Dict, List, Any

# Table schemas based on the Project IA document
TABLE_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "RM_AGGREGATED_DATA": {
        "description": "Main aggregated data table containing communication session records",
        "columns": {
            "AP_ID": {
                "type": "UInt32",
                "description": "Technical identifier of the line"
            },
            "PARTY_ID": {
                "type": "UInt32",
                "description": "Technical identifier of the client"
            },
            "PDP_CONNECTION_ID": {
                "type": "UInt32",
                "description": "Technical identifier of the DATA session"
            },
            "RECORD_OPENING_TIME": {
                "type": "DateTime('Europe/Paris')",
                "description": "Start date of the communication ticket"
            },
            "RECORD_CLOSING_TIME": {
                "type": "DateTime('Europe/Paris')",
                "description": "End date of the communication ticket"
            },
            "UPLOAD": {
                "type": "Int32",
                "description": "Upload volume in bytes"
            },
            "DOWNLOAD": {
                "type": "Int32",
                "description": "Download volume in bytes"
            },
            "DURATION": {
                "type": "Int32",
                "description": "Duration in minutes (maximum 15 minutes)"
            },
            "PLMN": {
                "type": "LowCardinality(String)",
                "description": "Mobile operator code"
            },
            "OFFER_CODE": {
                "type": "LowCardinality(String)",
                "description": "Tariff offer code of the line"
            },
            "SEQUENCE_NUMBER": {
                "type": "Int32",
                "description": "Sequential number of the ticket in the DATA session"
            },
            "CONNECTION_STATUS": {
                "type": "FixedString(1)",
                "description": "P: Partial (intermediate ticket), F: Final (final ticket)"
            },
            "IP_V4_ADDRESS": {
                "type": "String",
                "description": "IPv4 address of the communicating device"
            },
            "IP_V6_ADDRESS": {
                "type": "String",
                "description": "IPv6 address of the communicating device"
            },
            "IP_ADDRESS_TYPE": {
                "type": "FixedString(1)",
                "description": "IP address type: 1 (IPv4), 2 (IPv6), 3 (IPv4 or IPv6)"
            },
            "IMEI": {
                "type": "String",
                "description": "Identifier of the communicating device"
            },
            "IMSI": {
                "type": "UInt64",
                "description": "SIM card identifier contained in the communicating device"
            },
            "MSISDN": {
                "type": "String",
                "description": "Phone number of the line"
            },
            "APN": {
                "type": "String",
                "description": "Access Point Name"
            },
            "CELL_ID": {
                "type": "FixedString(8)",
                "description": "Technical identifier of the antenna through which communication passed"
            },
            "TICKET_GENERATION": {
                "type": "LowCardinality(String)",
                "description": "Generation type (2G, 3G, 4G, NBIOT, LTEM, etc.)"
            }
        }
    },
    "PLMN": {
        "description": "Mobile operator information table",
        "columns": {
            "PLMN": {
                "type": "String",
                "description": "PLMN code"
            },
            "PROVIDER": {
                "type": "String",
                "description": "Operator name"
            },
            "COUNTRY_ISO3": {
                "type": "String",
                "description": "ISO3 country code"
            }
        }
    },
    "CELL": {
        "description": "Cell tower/antenna information table",
        "columns": {
            "CELL_ID": {
                "type": "FixedString(8)",
                "description": "Antenna identifier"
            },
            "PLMN": {
                "type": "String",
                "description": "PLMN code"
            },
            "LONGITUDE": {
                "type": "Decimal(19,16)",
                "description": "GPS longitude coordinate"
            },
            "LATITUDE": {
                "type": "Decimal(19,16)",
                "description": "GPS latitude coordinate"
            }
        }
    },
    "CUSTOMER": {
        "description": "Customer information table",
        "columns": {
            "PARTY_ID": {
                "type": "UInt32",
                "description": "Technical identifier of the client"
            },
            "NAME": {
                "type": "String",
                "description": "Customer name"
            }
        }
    }
}

# Common query patterns and aliases
QUERY_PATTERNS = {
    "data_usage": ["upload", "download", "volume", "data", "traffic", "bytes"],
    "duration": ["duration", "time", "session", "minutes"],
    "customer": ["client", "customer", "user", "subscriber"],
    "location": ["location", "antenna", "cell", "tower", "coordinates", "GPS"],
    "operator": ["operator", "provider", "network", "PLMN"],
    "device": ["device", "phone", "mobile", "IMEI", "IMSI"],
    "generation": ["2G", "3G", "4G", "LTE", "NBIOT", "generation", "technology"]
}

# Relationship mappings between tables
TABLE_RELATIONSHIPS = {
    "RM_AGGREGATED_DATA": {
        "PLMN": "PLMN",
        "CELL": "CELL_ID",
        "CUSTOMER": "PARTY_ID"
    }
}

def get_table_schema(table_name: str) -> Dict[str, Any]:
    """Get schema for a specific table."""
    return TABLE_SCHEMAS.get(table_name.upper(), {})

def get_all_tables() -> List[str]:
    """Get list of all available tables."""
    return list(TABLE_SCHEMAS.keys())

def find_relevant_tables(keywords: List[str]) -> List[str]:
    """Find tables relevant to given keywords."""
    relevant_tables = set()

    for keyword in keywords:
        keyword_lower = keyword.lower()

        # Check each table and its columns
        for table_name, schema in TABLE_SCHEMAS.items():
            # Check table description
            if keyword_lower in schema.get("description", "").lower():
                relevant_tables.add(table_name)

            # Check column names and descriptions
            for col_name, col_info in schema.get("columns", {}).items():
                if (keyword_lower in col_name.lower() or
                        keyword_lower in col_info.get("description", "").lower()):
                    relevant_tables.add(table_name)

    return list(relevant_tables)

def get_column_suggestions(query_text: str) -> Dict[str, List[str]]:
    """Get column suggestions based on query text."""
    suggestions = {}
    query_lower = query_text.lower()

    for pattern, keywords in QUERY_PATTERNS.items():
        for keyword in keywords:
            if keyword in query_lower:
                suggestions[pattern] = []

                # Find relevant columns
                for table_name, schema in TABLE_SCHEMAS.items():
                    for col_name, col_info in schema.get("columns", {}).items():
                        if (keyword in col_name.lower() or
                                keyword in col_info.get("description", "").lower()):
                            suggestions[pattern].append(f"{table_name}.{col_name}")

    return suggestions