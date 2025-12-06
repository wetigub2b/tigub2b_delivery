"""
Helper Utilities

Utility functions for the delivery system including:
- Snowflake ID generation for distributed system
- File upload helpers
- Status validation helpers
- Common business logic utilities
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import List


# Snowflake ID Generator Configuration
# Based on Twitter's Snowflake algorithm for distributed unique IDs
#
# ID Structure (64 bits):
# - 1 bit: Sign bit (always 0)
# - 41 bits: Timestamp (milliseconds since epoch)
# - 10 bits: Machine ID (supports 1024 machines)
# - 12 bits: Sequence number (4096 IDs per millisecond per machine)

EPOCH = 1577836800000  # 2020-01-01 00:00:00 UTC in milliseconds
MACHINE_ID_BITS = 10
SEQUENCE_BITS = 12
MAX_MACHINE_ID = (1 << MACHINE_ID_BITS) - 1
MAX_SEQUENCE = (1 << SEQUENCE_BITS) - 1

# Default machine ID (should be configured per deployment)
MACHINE_ID = 1  # TODO: Set this from environment variable


class SnowflakeIDGenerator:
    """
    Thread-safe Snowflake ID generator for distributed systems.

    Generates unique 64-bit IDs consisting of:
    - Timestamp (milliseconds)
    - Machine ID
    - Sequence number

    Usage:
        generator = SnowflakeIDGenerator(machine_id=1)
        unique_id = generator.generate()
    """

    def __init__(self, machine_id: int = MACHINE_ID):
        """
        Initialize Snowflake ID generator.

        Args:
            machine_id: Unique identifier for this machine (0-1023)

        Raises:
            ValueError: If machine_id is out of range
        """
        if machine_id < 0 or machine_id > MAX_MACHINE_ID:
            raise ValueError(f"Machine ID must be between 0 and {MAX_MACHINE_ID}")

        self.machine_id = machine_id
        self.sequence = 0
        self.last_timestamp = -1

    def generate(self) -> int:
        """
        Generate unique Snowflake ID.

        Returns:
            Unique 64-bit integer ID

        Raises:
            RuntimeError: If clock moves backwards
        """
        timestamp = self._current_millis()

        # Clock moved backwards - this should not happen
        if timestamp < self.last_timestamp:
            raise RuntimeError(
                f"Clock moved backwards. Refusing to generate ID for "
                f"{self.last_timestamp - timestamp} milliseconds"
            )

        # Same millisecond - increment sequence
        if timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & MAX_SEQUENCE
            # Sequence overflow - wait for next millisecond
            if self.sequence == 0:
                timestamp = self._wait_next_millis(self.last_timestamp)
        else:
            self.sequence = 0

        self.last_timestamp = timestamp

        # Construct ID
        snowflake_id = (
            ((timestamp - EPOCH) << (MACHINE_ID_BITS + SEQUENCE_BITS))
            | (self.machine_id << SEQUENCE_BITS)
            | self.sequence
        )

        return snowflake_id

    @staticmethod
    def _current_millis() -> int:
        """Get current timestamp in milliseconds."""
        return int(time.time() * 1000)

    def _wait_next_millis(self, last_timestamp: int) -> int:
        """Wait until next millisecond."""
        timestamp = self._current_millis()
        while timestamp <= last_timestamp:
            timestamp = self._current_millis()
        return timestamp


# Global generator instance (single machine ID for entire application)
_generator = SnowflakeIDGenerator(machine_id=MACHINE_ID)


def generate_snowflake_id() -> int:
    """
    Generate unique Snowflake ID using global generator.

    Convenience function for generating IDs without managing generator instance.

    Returns:
        Unique 64-bit integer ID

    Example:
        action_id = generate_snowflake_id()
    """
    return _generator.generate()


def parse_snowflake_id(snowflake_id: int) -> dict:
    """
    Parse Snowflake ID into components.

    Args:
        snowflake_id: Snowflake ID to parse

    Returns:
        Dict with timestamp, machine_id, sequence, and datetime

    Example:
        info = parse_snowflake_id(123456789012345)
        print(info["datetime"])  # 2020-01-15 10:30:45.123
    """
    # Extract components
    sequence = snowflake_id & MAX_SEQUENCE
    machine_id = (snowflake_id >> SEQUENCE_BITS) & MAX_MACHINE_ID
    timestamp_ms = (snowflake_id >> (MACHINE_ID_BITS + SEQUENCE_BITS)) + EPOCH

    # Convert to datetime
    dt = datetime.fromtimestamp(timestamp_ms / 1000.0)

    return {
        "timestamp_ms": timestamp_ms,
        "machine_id": machine_id,
        "sequence": sequence,
        "datetime": dt,
    }


# Status Validation Helpers

def validate_shipping_status(status: int) -> bool:
    """
    Validate shipping status value.

    Valid shipping status values:
    0 = 待备货 (Pending Prepare)
    1 = 已备货 (Prepared)
    2 = 司机收货中 (Driver Pickup)
    3 = 司机送达仓库 (Driver to Warehouse)
    4 = 仓库已收货 (Warehouse Received)
    5 = 司机配送用户 (Driver to User)
    6 = 已送达 (Delivered)
    7 = 完成 (Complete)

    Args:
        status: Shipping status code

    Returns:
        True if valid, False otherwise
    """
    return 0 <= status <= 7


def validate_prepare_status(status: int | None) -> bool:
    """
    Validate prepare status value.

    Valid prepare status values:
    None = 待备货 (Pending Prepare)
    0 = 已备货 (Prepared)
    1 = 司机收货中 (Driver Pickup)
    2 = 司机送达仓库 (Driver to Warehouse)
    3 = 仓库已收货 (Warehouse Received)
    4 = 司机配送用户 (Driver to User)
    5 = 已送达 (Delivered)
    6 = 完成 (Complete)

    Args:
        status: Prepare status code (None or 0-6)

    Returns:
        True if valid, False otherwise
    """
    return status is None or (0 <= status <= 6)


def validate_action_type(action_type: int) -> bool:
    """
    Validate OrderAction action_type value.

    Valid action types:
    0 = 备货 (Goods Prepared)
    1 = 司机收货 (Driver Pickup)
    2 = 司机送达仓库 (Driver to Warehouse)
    3 = 仓库收货 (Warehouse Receive)
    4 = 仓库发货 (Warehouse Ship)
    5 = 完成 (Complete)
    6-11 = Refund/return workflow

    Args:
        action_type: Action type code

    Returns:
        True if valid, False otherwise
    """
    return 0 <= action_type <= 11


def validate_delivery_type(delivery_type: int) -> bool:
    """
    Validate delivery_type value.

    Valid delivery types:
    0 = 商家自配 (Merchant self-delivery)
    1 = 第三方配送 (Third-party driver delivery)

    Args:
        delivery_type: Delivery type code

    Returns:
        True if valid, False otherwise
    """
    return delivery_type in (0, 1)


def validate_shipping_type(shipping_type: int) -> bool:
    """
    Validate shipping_type value.

    Valid shipping types:
    0 = 发用户 (Ship to user)
    1 = 发仓库 (Ship to warehouse)

    Args:
        shipping_type: Shipping type code

    Returns:
        True if valid, False otherwise
    """
    return shipping_type in (0, 1)


def validate_status_transition(
    from_status: int, to_status: int, allow_skip: bool = False
) -> bool:
    """
    Validate status transition is allowed.

    By default, only sequential transitions are allowed (e.g., 0→1→2→3).
    Set allow_skip=True to allow skipping intermediate states.

    Args:
        from_status: Current status
        to_status: Target status
        allow_skip: Allow skipping intermediate states

    Returns:
        True if transition is valid, False otherwise

    Example:
        # Sequential transition
        validate_status_transition(1, 2)  # True (1→2)
        validate_status_transition(1, 3)  # False (cannot skip 2)

        # With skip allowed
        validate_status_transition(1, 3, allow_skip=True)  # True
    """
    # Status can only increase
    if to_status <= from_status:
        return False

    # Check if transition is sequential or skip is allowed
    if allow_skip:
        return to_status > from_status
    else:
        return to_status == from_status + 1


# File Helper Functions

def parse_file_id_list(file_ids_str: str | None) -> List[int]:
    """
    Parse comma-separated file IDs string into list of integers.

    Args:
        file_ids_str: Comma-separated string of file IDs (e.g., "123,456,789")

    Returns:
        List of integer file IDs

    Example:
        ids = parse_file_id_list("123,456,789")  # [123, 456, 789]
    """
    if not file_ids_str:
        return []

    try:
        return [int(fid.strip()) for fid in file_ids_str.split(",") if fid.strip()]
    except ValueError:
        return []


def format_file_id_list(file_ids: List[int]) -> str:
    """
    Format list of file IDs into comma-separated string.

    Args:
        file_ids: List of integer file IDs

    Returns:
        Comma-separated string

    Example:
        ids_str = format_file_id_list([123, 456, 789])  # "123,456,789"
    """
    return ",".join(str(fid) for fid in file_ids)


def parse_order_id_list(order_ids_str: str) -> List[int]:
    """
    Parse comma-separated order IDs string into list of integers.

    Args:
        order_ids_str: Comma-separated string of order IDs

    Returns:
        List of integer order IDs

    Example:
        ids = parse_order_id_list("101,102,103")  # [101, 102, 103]
    """
    try:
        return [int(oid.strip()) for oid in order_ids_str.split(",") if oid.strip()]
    except ValueError:
        return []


def format_order_id_list(order_ids: List[int]) -> str:
    """
    Format list of order IDs into comma-separated string.

    Args:
        order_ids: List of integer order IDs

    Returns:
        Comma-separated string

    Example:
        ids_str = format_order_id_list([101, 102, 103])  # "101,102,103"
    """
    return ",".join(str(oid) for oid in order_ids)


# Workflow Validation Helpers

def get_workflow_type(delivery_type: int, shipping_type: int) -> int:
    """
    Determine workflow type from delivery_type and shipping_type.

    Workflow Types:
    1 = 商家→用户 (Merchant self-delivery to user)
    2 = 商家→司机→仓库→用户 (Merchant→Driver→Warehouse→User)
    3 = 商家→司机→用户 (Merchant→Driver→User, third-party)
    4 = 商家→仓库 (Merchant→Warehouse only)

    Args:
        delivery_type: 0=Merchant, 1=Third-party
        shipping_type: 0=To user, 1=To warehouse

    Returns:
        Workflow type (1-4)

    Example:
        workflow = get_workflow_type(delivery_type=0, shipping_type=0)
        # Returns 1 (Merchant self-delivery to user)
    """
    if delivery_type == 0 and shipping_type == 0:
        return 1  # Merchant → User
    elif delivery_type == 1 and shipping_type == 1:
        return 2  # Merchant → Driver → Warehouse → User
    elif delivery_type == 1 and shipping_type == 0:
        return 3  # Merchant → Driver → User
    elif delivery_type == 0 and shipping_type == 1:
        return 4  # Merchant → Warehouse (special case)
    else:
        raise ValueError(f"Invalid delivery/shipping type combination: {delivery_type}/{shipping_type}")


def get_workflow_description(workflow_type: int) -> str:
    """
    Get human-readable workflow description.

    Args:
        workflow_type: Workflow type (1-4)

    Returns:
        Workflow description string

    Example:
        desc = get_workflow_description(2)
        # "商家→司机→仓库→用户 (Merchant→Driver→Warehouse→User)"
    """
    descriptions = {
        1: "商家→用户 (Merchant self-delivery to user)",
        2: "商家→司机→仓库→用户 (Merchant→Driver→Warehouse→User)",
        3: "商家→司机→用户 (Merchant→Driver→User, third-party)",
        4: "商家→仓库 (Merchant→Warehouse only)",
    }
    return descriptions.get(workflow_type, "Unknown workflow")


def get_expected_statuses_for_workflow(workflow_type: int) -> List[int]:
    """
    Get list of expected shipping statuses for a workflow type.

    Args:
        workflow_type: Workflow type (1-4)

    Returns:
        List of shipping status codes expected in this workflow

    Example:
        statuses = get_expected_statuses_for_workflow(2)
        # [0, 1, 2, 3, 4, 5, 6, 7] (all statuses for full workflow)
    """
    if workflow_type == 1:
        # Merchant → User: 0→1→6→7
        return [0, 1, 6, 7]
    elif workflow_type == 2:
        # Merchant → Driver → Warehouse → User: All statuses
        return [0, 1, 2, 3, 4, 5, 6, 7]
    elif workflow_type == 3:
        # Merchant → Driver → User: 0→1→2→6→7
        return [0, 1, 2, 6, 7]
    elif workflow_type == 4:
        # Merchant → Warehouse: 0→1→2→3→4
        return [0, 1, 2, 3, 4]
    else:
        raise ValueError(f"Invalid workflow type: {workflow_type}")
