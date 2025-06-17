"""
Enhanced database schemas and metadata with better relationship mapping.
"""

# Table schemas with enhanced metadata
TABLE_SCHEMAS = {
    "RM_AGGREGATED_DATA": {
        "description": "Main aggregated data table containing communication session records and tickets",
        "primary_key": "AP_ID",
        "business_context": "Core table for telecom data analysis - contains all communication sessions with volume, duration, and technical details",
        "common_queries": ["data usage analysis", "session duration", "device tracking", "operator statistics"],
        "columns": {
            "AP_ID": {
                "type": "UInt32",
                "description": "Technical identifier of the line",
                "is_primary_key": True
            },
            "PARTY_ID": {
                "type": "UInt32",
                "description": "Technical identifier of the client",
                "foreign_key": "CUSTOMER.PARTY_ID",
                "business_meaning": "Links to customer information"
            },
            "PDP_CONNECTION_ID": {
                "type": "UInt32",
                "description": "Technical identifier of the DATA session"
            },
            "RECORD_OPENING_TIME": {
                "type": "DateTime('Europe/Paris')",
                "description": "Start date of the communication ticket",
                "is_temporal": True,
                "common_filters": ["date ranges", "recent data", "time periods"]
            },
            "RECORD_CLOSING_TIME": {
                "type": "DateTime('Europe/Paris')",
                "description": "End date of the communication ticket",
                "is_temporal": True
            },
            "UPLOAD": {
                "type": "Int32",
                "description": "Upload volume in bytes",
                "unit": "bytes",
                "aggregatable": True,
                "business_meaning": "Data transmitted from device to network"
            },
            "DOWNLOAD": {
                "type": "Int32",
                "description": "Download volume in bytes",
                "unit": "bytes",
                "aggregatable": True,
                "business_meaning": "Data received by device from network"
            },
            "DURATION": {
                "type": "Int32",
                "description": "Duration in minutes (maximum 15 minutes)",
                "unit": "minutes",
                "aggregatable": True
            },
            "PLMN": {
                "type": "LowCardinality(String)",
                "description": "Mobile operator code",
                "foreign_key": "PLMN.PLMN",
                "business_meaning": "Links to operator and country information"
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
                "description": "P: Partial (intermediate ticket), F: Final (final ticket)",
                "enum_values": {"P": "Partial", "F": "Final"}
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
                "description": "IP address type: 1 (IPv4), 2 (IPv6), 3 (IPv4 or IPv6)",
                "enum_values": {"1": "IPv4", "2": "IPv6", "3": "IPv4 or IPv6"}
            },
            "IMEI": {
                "type": "String",
                "description": "Identifier of the communicating device",
                "business_meaning": "Unique device identifier for tracking"
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
                "description": "Technical identifier of the antenna through which communication passed",
                "foreign_key": "CELL.CELL_ID",
                "business_meaning": "Links to geographic location information"
            },
            "TICKET_GENERATION": {
                "type": "LowCardinality(String)",
                "description": "Generation type (2G, 3G, 4G, NBIOT, LTEM, etc.)",
                "business_meaning": "Technology used for communication"
            }
        }
    },
    "PLMN": {
        "description": "Mobile operator information table - links operators to countries",
        "primary_key": "PLMN",
        "business_context": "Reference table for geographic analysis - essential for country-based queries",
        "common_queries": ["country analysis", "operator distribution", "geographic statistics"],
        "columns": {
            "PLMN": {
                "type": "String",
                "description": "PLMN code (unique identifier for mobile network operators)",
                "is_primary_key": True,
                "business_meaning": "Mobile Network Code - identifies operator and country"
            },
            "PROVIDER": {
                "type": "String",
                "description": "Operator name (human-readable operator name)",
                "business_meaning": "Commercial name of the mobile operator"
            },
            "COUNTRY_ISO3": {
                "type": "String",
                "description": "ISO3 country code (3-letter country identifier)",
                "business_meaning": "Geographic location - use this for country-based analysis",
                "is_geographic": True
            }
        }
    },
    "CELL": {
        "description": "Cell tower/antenna information table - provides geographic coordinates",
        "primary_key": "CELL_ID",
        "business_context": "Geographic reference table for precise location analysis",
        "common_queries": ["location analysis", "antenna coverage", "geographic distribution"],
        "columns": {
            "CELL_ID": {
                "type": "FixedString(8)",
                "description": "Antenna identifier (unique cell tower ID)",
                "is_primary_key": True
            },
            "PLMN": {
                "type": "String",
                "description": "PLMN code",
                "foreign_key": "PLMN.PLMN",
                "business_meaning": "Links cell to operator and country"
            },
            "LONGITUDE": {
                "type": "Decimal(19,16)",
                "description": "GPS longitude coordinate",
                "is_geographic": True,
                "unit": "degrees"
            },
            "LATITUDE": {
                "type": "Decimal(19,16)",
                "description": "GPS latitude coordinate",
                "is_geographic": True,
                "unit": "degrees"
            }
        }
    },
    "CUSTOMER": {
        "description": "Customer information table - basic customer data",
        "primary_key": "PARTY_ID",
        "business_context": "Customer reference table for customer-based analysis",
        "common_queries": ["customer analysis", "customer count", "customer identification"],
        "columns": {
            "PARTY_ID": {
                "type": "UInt32",
                "description": "Technical identifier of the client (unique customer ID)",
                "is_primary_key": True
            },
            "NAME": {
                "type": "String",
                "description": "Customer name (commercial or technical name)"
            }
        }
    }
}

# Enhanced relationship definitions with join patterns
TABLE_RELATIONSHIPS = {
    "RM_AGGREGATED_DATA": {
        "joins_to": {
            "PLMN": {
                "join_key": "PLMN",
                "relationship": "many_to_one",
                "purpose": "Get operator and country information",
                "join_sql": "RM_AGGREGATED_DATA r JOIN PLMN p ON r.PLMN = p.PLMN"
            },
            "CELL": {
                "join_key": "CELL_ID",
                "relationship": "many_to_one",
                "purpose": "Get precise geographic coordinates",
                "join_sql": "RM_AGGREGATED_DATA r JOIN CELL c ON r.CELL_ID = c.CELL_ID"
            },
            "CUSTOMER": {
                "join_key": "PARTY_ID",
                "relationship": "many_to_one",
                "purpose": "Get customer information",
                "join_sql": "RM_AGGREGATED_DATA r JOIN CUSTOMER cust ON r.PARTY_ID = cust.PARTY_ID"
            }
        }
    },
    "CELL": {
        "joins_to": {
            "PLMN": {
                "join_key": "PLMN",
                "relationship": "many_to_one",
                "purpose": "Get operator and country for cell location",
                "join_sql": "CELL c JOIN PLMN p ON c.PLMN = p.PLMN"
            }
        }
    }
}

# Query patterns with enhanced context
QUERY_PATTERNS = {
    "geographic_analysis": {
        "keywords": ["country", "geographic", "location", "répartition géographique", "pays", "region"],
        "requires_tables": ["RM_AGGREGATED_DATA", "PLMN"],
        "key_columns": ["PLMN.COUNTRY_ISO3"],
        "common_joins": "RM_AGGREGATED_DATA r JOIN PLMN p ON r.PLMN = p.PLMN",
        "example_sql": "SELECT p.COUNTRY_ISO3, COUNT(*) FROM RM_AGGREGATED_DATA r JOIN PLMN p ON r.PLMN = p.PLMN GROUP BY p.COUNTRY_ISO3"
    },
    "data_usage": {
        "keywords": ["upload", "download", "volume", "data", "traffic", "bytes", "usage"],
        "requires_tables": ["RM_AGGREGATED_DATA"],
        "key_columns": ["UPLOAD", "DOWNLOAD"],
        "aggregations": ["SUM", "AVG", "MAX"],
        "example_sql": "SELECT SUM(UPLOAD + DOWNLOAD) as total_data FROM RM_AGGREGATED_DATA"
    },
    "temporal_analysis": {
        "keywords": ["time", "date", "period", "recent", "last", "yesterday", "today", "journées", "dernières"],
        "requires_tables": ["RM_AGGREGATED_DATA"],
        "key_columns": ["RECORD_OPENING_TIME", "RECORD_CLOSING_TIME"],
        "common_filters": "WHERE RECORD_OPENING_TIME >= now() - INTERVAL X DAY",
        "example_sql": "SELECT * FROM RM_AGGREGATED_DATA WHERE RECORD_OPENING_TIME >= now() - INTERVAL 2 DAY"
    },
    "operator_analysis": {
        "keywords": ["operator", "provider", "network", "PLMN", "opérateur"],
        "requires_tables": ["RM_AGGREGATED_DATA", "PLMN"],
        "key_columns": ["PLMN.PROVIDER"],
        "common_joins": "RM_AGGREGATED_DATA r JOIN PLMN p ON r.PLMN = p.PLMN"
    },
    "customer_analysis": {
        "keywords": ["customer", "client", "user", "subscriber", "customers"],
        "requires_tables": ["RM_AGGREGATED_DATA", "CUSTOMER"],
        "key_columns": ["CUSTOMER.NAME", "CUSTOMER.PARTY_ID"],
        "common_joins": "RM_AGGREGATED_DATA r JOIN CUSTOMER c ON r.PARTY_ID = c.PARTY_ID"
    }
}

# Business scenarios with SQL templates
BUSINESS_SCENARIOS = {
    "geographic_distribution": {
        "description": "Analyze data distribution by country",
        "keywords": ["geographic", "country", "distribution", "répartition", "pays"],
        "sql_template": """
        SELECT 
            p.COUNTRY_ISO3 as country,
            COUNT(*) * 100.0 / (SELECT COUNT(*) FROM RM_AGGREGATED_DATA {time_filter}) as percentage
        FROM RM_AGGREGATED_DATA r
        JOIN PLMN p ON r.PLMN = p.PLMN
        {time_filter}
        GROUP BY p.COUNTRY_ISO3
        ORDER BY percentage DESC
        LIMIT {limit}
        """,
        "required_tables": ["RM_AGGREGATED_DATA", "PLMN"]
    },
    "data_usage_by_country": {
        "description": "Analyze data consumption by country",
        "keywords": ["data", "usage", "country", "consumption"],
        "sql_template": """
        SELECT 
            p.COUNTRY_ISO3 as country,
            SUM(r.UPLOAD + r.DOWNLOAD) as total_data,
            AVG(r.UPLOAD + r.DOWNLOAD) as avg_data
        FROM RM_AGGREGATED_DATA r
        JOIN PLMN p ON r.PLMN = p.PLMN
        {time_filter}
        GROUP BY p.COUNTRY_ISO3
        ORDER BY total_data DESC
        LIMIT {limit}
        """,
        "required_tables": ["RM_AGGREGATED_DATA", "PLMN"]
    }
}