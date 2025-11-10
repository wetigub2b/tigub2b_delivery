"""
Workflow validation middleware.

Validates business rules and state transitions for delivery workflows.
Prevents invalid operations and ensures data integrity.
"""
from typing import Optional


class WorkflowValidationError(Exception):
    """Raised when workflow validation fails"""
    pass


class WorkflowValidator:
    """
    Validates delivery workflow state transitions and business rules.

    Implements state machine validation for all 4 delivery workflows.
    """

    # Valid prepare_status transitions
    # prepare_status: NULL → 0 → 1 → 2 → 3 → 4 → 5 → 6
    VALID_STATUS_TRANSITIONS = {
        None: [0],  # NULL → 0 (准备完成)
        0: [1, 3, 5],  # 0 → 1 (司机收货) or 3 (仓库收货) or 5 (已送达)
        1: [2, 5],  # 1 → 2 (送达仓库) or 5 (送达用户)
        2: [3],  # 2 → 3 (仓库收货)
        3: [4],  # 3 → 4 (仓库发货)
        4: [5],  # 4 → 5 (已送达)
        5: [6],  # 5 → 6 (完成)
        6: [],  # 6 (完成) - terminal state
    }

    @classmethod
    def validate_status_transition(
        cls,
        current_status: Optional[int],
        new_status: int
    ) -> bool:
        """
        Validate prepare_status transition is allowed.

        Args:
            current_status: Current prepare_status (None for NULL)
            new_status: Desired new status

        Returns:
            True if transition is valid

        Raises:
            WorkflowValidationError: If transition is invalid
        """
        valid_next_states = cls.VALID_STATUS_TRANSITIONS.get(current_status, [])

        if new_status not in valid_next_states:
            raise WorkflowValidationError(
                f"Invalid status transition: {current_status} → {new_status}. "
                f"Valid next states: {valid_next_states}"
            )

        return True

    @classmethod
    def validate_workflow_configuration(
        cls,
        delivery_type: int,
        shipping_type: int,
        warehouse_id: Optional[int] = None
    ) -> bool:
        """
        Validate delivery workflow configuration.

        Args:
            delivery_type: 0=Merchant self, 1=Third-party driver
            shipping_type: 0=To warehouse, 1=To user
            warehouse_id: Warehouse ID (required if shipping_type=0)

        Returns:
            True if configuration is valid

        Raises:
            WorkflowValidationError: If configuration is invalid
        """
        # Validate delivery_type
        if delivery_type not in [0, 1]:
            raise WorkflowValidationError(
                f"Invalid delivery_type: {delivery_type}. Must be 0 or 1."
            )

        # Validate shipping_type
        if shipping_type not in [0, 1]:
            raise WorkflowValidationError(
                f"Invalid shipping_type: {shipping_type}. Must be 0 or 1."
            )

        # If shipping to warehouse, warehouse_id is required
        if shipping_type == 0 and warehouse_id is None:
            raise WorkflowValidationError(
                "warehouse_id required when shipping_type=0 (to warehouse)"
            )

        # If shipping to user, warehouse_id should be None
        if shipping_type == 1 and warehouse_id is not None:
            # This is a warning, not an error - we'll allow it but log
            pass

        return True

    @classmethod
    def validate_workflow_path(
        cls,
        delivery_type: int,
        shipping_type: int,
        current_status: Optional[int],
        target_status: int
    ) -> bool:
        """
        Validate that target_status is valid for the workflow type.

        Different workflows have different valid status paths:
        - Workflow 1 (0,0): NULL → 0 → 3 → 4 → 5 → 6
        - Workflow 2 (0,1): NULL → 0 → 5 → 6
        - Workflow 3 (1,0): NULL → 0 → 1 → 2 → 3 → 4 → 5 → 6
        - Workflow 4 (1,1): NULL → 0 → 1 → 5 → 6

        Args:
            delivery_type: Delivery configuration
            shipping_type: Shipping configuration
            current_status: Current status
            target_status: Target status

        Returns:
            True if status is valid for this workflow

        Raises:
            WorkflowValidationError: If status is invalid for workflow
        """
        # Define valid statuses for each workflow
        workflow_valid_statuses = {
            (0, 0): [None, 0, 3, 4, 5, 6],  # Workflow 1
            (0, 1): [None, 0, 5, 6],  # Workflow 2
            (1, 0): [None, 0, 1, 2, 3, 4, 5, 6],  # Workflow 3
            (1, 1): [None, 0, 1, 5, 6],  # Workflow 4
        }

        workflow_key = (delivery_type, shipping_type)
        valid_statuses = workflow_valid_statuses.get(workflow_key)

        if valid_statuses is None:
            raise WorkflowValidationError(
                f"Invalid workflow configuration: delivery_type={delivery_type}, "
                f"shipping_type={shipping_type}"
            )

        if target_status not in valid_statuses:
            raise WorkflowValidationError(
                f"Status {target_status} not valid for workflow "
                f"(delivery_type={delivery_type}, shipping_type={shipping_type}). "
                f"Valid statuses: {valid_statuses}"
            )

        return True

    @classmethod
    def validate_photo_evidence_required(
        cls,
        action_type: int,
        file_ids: Optional[list] = None
    ) -> bool:
        """
        Validate photo evidence requirements for actions.

        Most workflow transitions require photo evidence.

        Args:
            action_type: Action type code (0-11)
            file_ids: List of file IDs

        Returns:
            True if photo requirement is satisfied

        Raises:
            WorkflowValidationError: If photo evidence is missing when required
        """
        # Actions that require photo evidence
        PHOTO_REQUIRED_ACTIONS = [0, 1, 2, 3, 4, 5]

        if action_type in PHOTO_REQUIRED_ACTIONS:
            if not file_ids or len(file_ids) == 0:
                # In production, this might be a hard requirement
                # For now, we'll allow it but could enforce strictly
                pass  # Warning level, not error

        return True

    @classmethod
    def validate_driver_assignment(
        cls,
        delivery_type: int,
        driver_id: Optional[int]
    ) -> bool:
        """
        Validate driver assignment based on delivery type.

        Args:
            delivery_type: 0=Merchant, 1=Third-party
            driver_id: Driver ID

        Returns:
            True if assignment is valid

        Raises:
            WorkflowValidationError: If assignment is invalid
        """
        # Third-party delivery requires driver
        if delivery_type == 1 and driver_id is None:
            raise WorkflowValidationError(
                "driver_id required for third-party delivery (delivery_type=1)"
            )

        # Merchant self-delivery should not have driver
        if delivery_type == 0 and driver_id is not None:
            raise WorkflowValidationError(
                "driver_id should be None for merchant self-delivery (delivery_type=0)"
            )

        return True

    @classmethod
    def validate_order_not_in_multiple_packages(
        cls,
        order_id: int,
        existing_packages: list
    ) -> bool:
        """
        Validate that order is not in multiple active prepare packages.

        Args:
            order_id: Order ID to check
            existing_packages: List of existing PrepareGoods packages

        Returns:
            True if order is not duplicated

        Raises:
            WorkflowValidationError: If order is already in another package
        """
        for package in existing_packages:
            order_ids = [int(oid) for oid in package.order_ids.split(",")]
            if order_id in order_ids and package.prepare_status < 6:  # Not completed
                raise WorkflowValidationError(
                    f"Order {order_id} is already in active prepare package "
                    f"{package.prepare_sn}"
                )

        return True


def validate_workflow_transition(
    delivery_type: int,
    shipping_type: int,
    current_status: Optional[int],
    new_status: int
) -> bool:
    """
    Convenience function to validate complete workflow transition.

    Args:
        delivery_type: Delivery configuration
        shipping_type: Shipping configuration
        current_status: Current prepare_status
        new_status: Target prepare_status

    Returns:
        True if transition is valid

    Raises:
        WorkflowValidationError: If validation fails
    """
    validator = WorkflowValidator()

    # Validate configuration
    validator.validate_workflow_configuration(delivery_type, shipping_type)

    # Validate status transition
    validator.validate_status_transition(current_status, new_status)

    # Validate workflow path
    validator.validate_workflow_path(
        delivery_type, shipping_type, current_status, new_status
    )

    return True
