"""
Utility Functions Package

Provides helper utilities for the delivery system:
- Snowflake ID generation for distributed systems
- File ID parsing and formatting
- Status validation
- Workflow type detection
"""

from app.utils.helpers import (
    # Snowflake ID functions
    SnowflakeIDGenerator,
    generate_snowflake_id,
    parse_snowflake_id,

    # Status validation
    validate_shipping_status,
    validate_prepare_status,
    validate_action_type,
    validate_delivery_type,
    validate_shipping_type,
    validate_status_transition,

    # File helpers
    parse_file_id_list,
    format_file_id_list,
    parse_order_id_list,
    format_order_id_list,

    # Workflow helpers
    get_workflow_type,
    get_workflow_description,
    get_expected_statuses_for_workflow,
)

__all__ = [
    # Snowflake ID
    "SnowflakeIDGenerator",
    "generate_snowflake_id",
    "parse_snowflake_id",

    # Status validation
    "validate_shipping_status",
    "validate_prepare_status",
    "validate_action_type",
    "validate_delivery_type",
    "validate_shipping_type",
    "validate_status_transition",

    # File helpers
    "parse_file_id_list",
    "format_file_id_list",
    "parse_order_id_list",
    "format_order_id_list",

    # Workflow helpers
    "get_workflow_type",
    "get_workflow_description",
    "get_expected_statuses_for_workflow",
]
