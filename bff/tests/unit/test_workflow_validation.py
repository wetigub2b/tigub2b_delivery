"""
Unit tests for workflow validation middleware.

Tests validation of:
- Status transitions
- Workflow configurations
- Business rules
- Photo evidence requirements
"""
import pytest

from app.middleware.workflow_validation import (
    WorkflowValidator,
    WorkflowValidationError,
    validate_workflow_transition
)


class TestStatusTransitionValidation:
    """Tests for status transition validation"""

    def test_valid_transition_null_to_0(self):
        """Test valid transition from NULL to 0 (prepared)"""
        assert WorkflowValidator.validate_status_transition(None, 0) is True

    def test_valid_transition_0_to_1(self):
        """Test valid transition from 0 to 1 (driver pickup)"""
        assert WorkflowValidator.validate_status_transition(0, 1) is True

    def test_valid_transition_1_to_2(self):
        """Test valid transition from 1 to 2 (driver to warehouse)"""
        assert WorkflowValidator.validate_status_transition(1, 2) is True

    def test_valid_transition_0_to_3(self):
        """Test valid transition from 0 to 3 (warehouse receive directly)"""
        assert WorkflowValidator.validate_status_transition(0, 3) is True

    def test_valid_transition_0_to_5(self):
        """Test valid transition from 0 to 5 (merchant direct delivery)"""
        assert WorkflowValidator.validate_status_transition(0, 5) is True

    def test_valid_transition_5_to_6(self):
        """Test valid transition from 5 to 6 (complete)"""
        assert WorkflowValidator.validate_status_transition(5, 6) is True

    def test_invalid_transition_null_to_3(self):
        """Test invalid transition from NULL to 3 (skip prepare)"""
        with pytest.raises(WorkflowValidationError) as exc_info:
            WorkflowValidator.validate_status_transition(None, 3)

        assert "Invalid status transition" in str(exc_info.value)
        assert "None → 3" in str(exc_info.value)

    def test_invalid_transition_0_to_4(self):
        """Test invalid transition from 0 to 4 (skip intermediate steps)"""
        with pytest.raises(WorkflowValidationError) as exc_info:
            WorkflowValidator.validate_status_transition(0, 4)

        assert "0 → 4" in str(exc_info.value)

    def test_invalid_transition_from_terminal_state(self):
        """Test that completed status (6) cannot transition"""
        with pytest.raises(WorkflowValidationError):
            WorkflowValidator.validate_status_transition(6, 0)

    def test_invalid_backward_transition(self):
        """Test that backward transitions are not allowed"""
        with pytest.raises(WorkflowValidationError):
            WorkflowValidator.validate_status_transition(5, 1)


class TestWorkflowConfigurationValidation:
    """Tests for workflow configuration validation"""

    def test_valid_workflow_1_config(self):
        """Test valid Workflow 1: Merchant → Warehouse"""
        assert WorkflowValidator.validate_workflow_configuration(
            delivery_type=0,
            shipping_type=0,
            warehouse_id=5
        ) is True

    def test_valid_workflow_2_config(self):
        """Test valid Workflow 2: Merchant → User"""
        assert WorkflowValidator.validate_workflow_configuration(
            delivery_type=0,
            shipping_type=1,
            warehouse_id=None
        ) is True

    def test_valid_workflow_3_config(self):
        """Test valid Workflow 3: Driver → Warehouse"""
        assert WorkflowValidator.validate_workflow_configuration(
            delivery_type=1,
            shipping_type=0,
            warehouse_id=5
        ) is True

    def test_valid_workflow_4_config(self):
        """Test valid Workflow 4: Driver → User"""
        assert WorkflowValidator.validate_workflow_configuration(
            delivery_type=1,
            shipping_type=1,
            warehouse_id=None
        ) is True

    def test_invalid_delivery_type(self):
        """Test invalid delivery_type value"""
        with pytest.raises(WorkflowValidationError) as exc_info:
            WorkflowValidator.validate_workflow_configuration(
                delivery_type=2,  # Invalid
                shipping_type=0,
                warehouse_id=5
            )

        assert "Invalid delivery_type: 2" in str(exc_info.value)

    def test_invalid_shipping_type(self):
        """Test invalid shipping_type value"""
        with pytest.raises(WorkflowValidationError) as exc_info:
            WorkflowValidator.validate_workflow_configuration(
                delivery_type=0,
                shipping_type=3,  # Invalid
                warehouse_id=None
            )

        assert "Invalid shipping_type: 3" in str(exc_info.value)

    def test_missing_warehouse_for_warehouse_shipping(self):
        """Test warehouse_id required when shipping_type=0"""
        with pytest.raises(WorkflowValidationError) as exc_info:
            WorkflowValidator.validate_workflow_configuration(
                delivery_type=1,
                shipping_type=0,  # To warehouse
                warehouse_id=None  # Missing!
            )

        assert "warehouse_id required" in str(exc_info.value)

    def test_warehouse_id_with_user_shipping(self):
        """Test warehouse_id with shipping_type=1 (warning, not error)"""
        # Should not raise error, just log warning
        assert WorkflowValidator.validate_workflow_configuration(
            delivery_type=0,
            shipping_type=1,  # To user
            warehouse_id=5  # Unnecessary but allowed
        ) is True


class TestWorkflowPathValidation:
    """Tests for workflow-specific status path validation"""

    def test_workflow_1_valid_statuses(self):
        """Test valid statuses for Workflow 1 (Merchant → Warehouse)"""
        # Workflow 1: NULL → 0 → 3 → 4 → 5 → 6
        valid_statuses = [None, 0, 3, 4, 5, 6]

        for status in valid_statuses:
            assert WorkflowValidator.validate_workflow_path(
                delivery_type=0,
                shipping_type=0,
                current_status=None,  # Not used in this validation
                target_status=status if status is not None else 0
            ) is True

    def test_workflow_1_invalid_status(self):
        """Test invalid status for Workflow 1 (no driver pickup)"""
        with pytest.raises(WorkflowValidationError) as exc_info:
            WorkflowValidator.validate_workflow_path(
                delivery_type=0,
                shipping_type=0,
                current_status=None,
                target_status=1  # Driver pickup not in workflow 1
            )

        assert "Status 1 not valid" in str(exc_info.value)

    def test_workflow_2_valid_statuses(self):
        """Test valid statuses for Workflow 2 (Merchant → User)"""
        # Workflow 2: NULL → 0 → 5 → 6 (shortest path)
        valid_statuses = [0, 5, 6]

        for status in valid_statuses:
            assert WorkflowValidator.validate_workflow_path(
                delivery_type=0,
                shipping_type=1,
                current_status=None,
                target_status=status
            ) is True

    def test_workflow_2_invalid_warehouse_status(self):
        """Test warehouse statuses invalid for Workflow 2"""
        # Workflow 2 should not have warehouse statuses (3, 4)
        with pytest.raises(WorkflowValidationError):
            WorkflowValidator.validate_workflow_path(
                delivery_type=0,
                shipping_type=1,
                current_status=0,
                target_status=3  # Warehouse receive not in workflow 2
            )

    def test_workflow_3_all_statuses(self):
        """Test Workflow 3 has all statuses (most complex)"""
        # Workflow 3: NULL → 0 → 1 → 2 → 3 → 4 → 5 → 6 (all steps)
        all_statuses = [0, 1, 2, 3, 4, 5, 6]

        for status in all_statuses:
            assert WorkflowValidator.validate_workflow_path(
                delivery_type=1,
                shipping_type=0,
                current_status=None,
                target_status=status
            ) is True

    def test_workflow_4_no_warehouse_statuses(self):
        """Test Workflow 4 does not have warehouse statuses"""
        # Workflow 4: NULL → 0 → 1 → 5 → 6 (no warehouse)
        with pytest.raises(WorkflowValidationError):
            WorkflowValidator.validate_workflow_path(
                delivery_type=1,
                shipping_type=1,
                current_status=1,
                target_status=2  # Driver to warehouse not in workflow 4
            )


class TestPhotoEvidenceValidation:
    """Tests for photo evidence requirements"""

    def test_photo_required_actions(self):
        """Test actions that require photo evidence"""
        required_actions = [0, 1, 2, 3, 4, 5]

        for action_type in required_actions:
            # Should not raise error, but logs warning
            assert WorkflowValidator.validate_photo_evidence_required(
                action_type=action_type,
                file_ids=[1001]  # Has photo
            ) is True

    def test_photo_missing_allowed(self):
        """Test that missing photo is currently allowed (warning level)"""
        # In production, you might make this a hard requirement
        assert WorkflowValidator.validate_photo_evidence_required(
            action_type=0,
            file_ids=None  # Missing photo
        ) is True

    def test_photo_not_required_for_refund_actions(self):
        """Test refund actions don't require photo"""
        refund_actions = [6, 7, 8, 9, 10, 11]

        for action_type in refund_actions:
            assert WorkflowValidator.validate_photo_evidence_required(
                action_type=action_type,
                file_ids=None
            ) is True


class TestDriverAssignmentValidation:
    """Tests for driver assignment validation"""

    def test_third_party_requires_driver(self):
        """Test third-party delivery requires driver_id"""
        with pytest.raises(WorkflowValidationError) as exc_info:
            WorkflowValidator.validate_driver_assignment(
                delivery_type=1,  # Third-party
                driver_id=None  # Missing driver!
            )

        assert "driver_id required" in str(exc_info.value)

    def test_third_party_with_driver_valid(self):
        """Test third-party with driver is valid"""
        assert WorkflowValidator.validate_driver_assignment(
            delivery_type=1,
            driver_id=10
        ) is True

    def test_merchant_should_not_have_driver(self):
        """Test merchant self-delivery should not have driver"""
        with pytest.raises(WorkflowValidationError) as exc_info:
            WorkflowValidator.validate_driver_assignment(
                delivery_type=0,  # Merchant
                driver_id=10  # Should not have driver
            )

        assert "should be None" in str(exc_info.value)

    def test_merchant_without_driver_valid(self):
        """Test merchant without driver is valid"""
        assert WorkflowValidator.validate_driver_assignment(
            delivery_type=0,
            driver_id=None
        ) is True


class TestOrderDuplicationValidation:
    """Tests for order duplication in packages"""

    def test_order_not_in_other_packages(self):
        """Test order can be added when not in other packages"""
        existing_packages = []

        assert WorkflowValidator.validate_order_not_in_multiple_packages(
            order_id=101,
            existing_packages=existing_packages
        ) is True

    def test_order_already_in_active_package(self):
        """Test error when order is in another active package"""
        from app.models.prepare_goods import PrepareGoods

        # Mock existing package
        existing_package = PrepareGoods(
            id=1,
            prepare_sn="PREP001",
            order_ids="101,102",
            delivery_type=1,
            shipping_type=0,
            prepare_status=1,  # Active (< 6)
            shop_id=1
        )

        with pytest.raises(WorkflowValidationError) as exc_info:
            WorkflowValidator.validate_order_not_in_multiple_packages(
                order_id=101,
                existing_packages=[existing_package]
            )

        assert "already in active prepare package" in str(exc_info.value)
        assert "PREP001" in str(exc_info.value)

    def test_order_in_completed_package_allowed(self):
        """Test order can be reused if previous package is completed"""
        from app.models.prepare_goods import PrepareGoods

        # Mock completed package
        completed_package = PrepareGoods(
            id=1,
            prepare_sn="PREP001",
            order_ids="101,102",
            delivery_type=1,
            shipping_type=0,
            prepare_status=6,  # Completed
            shop_id=1
        )

        assert WorkflowValidator.validate_order_not_in_multiple_packages(
            order_id=101,
            existing_packages=[completed_package]
        ) is True


class TestCompleteWorkflowTransitionValidation:
    """Tests for complete workflow transition validation"""

    def test_workflow_1_complete_transition(self):
        """Test complete valid transition for Workflow 1"""
        assert validate_workflow_transition(
            delivery_type=0,
            shipping_type=0,
            current_status=0,
            new_status=3
        ) is True

    def test_workflow_2_complete_transition(self):
        """Test complete valid transition for Workflow 2"""
        assert validate_workflow_transition(
            delivery_type=0,
            shipping_type=1,
            current_status=0,
            new_status=5
        ) is True

    def test_workflow_3_complete_transition(self):
        """Test complete valid transition for Workflow 3"""
        assert validate_workflow_transition(
            delivery_type=1,
            shipping_type=0,
            current_status=1,
            new_status=2
        ) is True

    def test_workflow_4_complete_transition(self):
        """Test complete valid transition for Workflow 4"""
        assert validate_workflow_transition(
            delivery_type=1,
            shipping_type=1,
            current_status=1,
            new_status=5
        ) is True

    def test_invalid_complete_transition(self):
        """Test invalid transition fails all validations"""
        with pytest.raises(WorkflowValidationError):
            validate_workflow_transition(
                delivery_type=0,
                shipping_type=1,
                current_status=0,
                new_status=3  # Warehouse status not valid for workflow 2
            )


class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_negative_status_values(self):
        """Test negative status values are invalid"""
        with pytest.raises(WorkflowValidationError):
            WorkflowValidator.validate_status_transition(0, -1)

    def test_status_beyond_range(self):
        """Test status values beyond valid range"""
        with pytest.raises(WorkflowValidationError):
            WorkflowValidator.validate_status_transition(0, 10)

    def test_same_status_transition(self):
        """Test transitioning to same status"""
        with pytest.raises(WorkflowValidationError):
            WorkflowValidator.validate_status_transition(0, 0)

    def test_empty_file_ids_list(self):
        """Test empty file_ids list"""
        assert WorkflowValidator.validate_photo_evidence_required(
            action_type=0,
            file_ids=[]  # Empty list
        ) is True
