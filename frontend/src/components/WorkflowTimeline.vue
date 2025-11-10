<template>
  <div class="workflow-timeline">
    <div class="timeline-header">
      <h4 class="timeline-title">{{ workflowLabel }}</h4>
      <div class="timeline-status">
        {{ currentStatusLabel }}
      </div>
    </div>

    <div class="timeline-steps">
      <!-- Workflow 1: Merchant → Warehouse → User (0,0) -->
      <template v-if="deliveryType === 0 && shippingType === 0">
        <WorkflowStep
          :completed="prepareStatus !== null && prepareStatus >= 0"
          :active="prepareStatus === 0"
          icon="📦"
          :label="$t('workflow.steps.merchantPrepared')"
        />
        <WorkflowStep
          :completed="prepareStatus !== null && prepareStatus >= 3"
          :active="prepareStatus === 3"
          icon="🏭"
          :label="$t('workflow.steps.warehouseReceived')"
        />
        <WorkflowStep
          :completed="prepareStatus !== null && prepareStatus >= 4"
          :active="prepareStatus === 4"
          icon="🚚"
          :label="$t('workflow.steps.warehouseShipped')"
        />
        <WorkflowStep
          :completed="prepareStatus !== null && prepareStatus >= 6"
          :active="prepareStatus === 6"
          icon="✅"
          :label="$t('workflow.steps.delivered')"
        />
      </template>

      <!-- Workflow 2: Merchant → User (0,1) -->
      <template v-else-if="deliveryType === 0 && shippingType === 1">
        <WorkflowStep
          :completed="prepareStatus !== null && prepareStatus >= 0"
          :active="prepareStatus === 0"
          icon="📦"
          :label="$t('workflow.steps.merchantPrepared')"
        />
        <WorkflowStep
          :completed="prepareStatus !== null && prepareStatus >= 5"
          :active="prepareStatus === 5"
          icon="🚚"
          :label="$t('workflow.steps.shipped')"
        />
        <WorkflowStep
          :completed="prepareStatus !== null && prepareStatus >= 6"
          :active="prepareStatus === 6"
          icon="✅"
          :label="$t('workflow.steps.delivered')"
        />
      </template>

      <!-- Workflow 3: Driver → Warehouse → User (1,0) -->
      <template v-else-if="deliveryType === 1 && shippingType === 0">
        <WorkflowStep
          :completed="prepareStatus !== null && prepareStatus >= 0"
          :active="prepareStatus === 0"
          icon="📦"
          :label="$t('workflow.steps.goodsReady')"
        />
        <WorkflowStep
          :completed="prepareStatus !== null && prepareStatus >= 1"
          :active="prepareStatus === 1"
          icon="🚗"
          :label="$t('workflow.steps.driverPickup')"
        />
        <WorkflowStep
          :completed="prepareStatus !== null && prepareStatus >= 2"
          :active="prepareStatus === 2"
          icon="🏭"
          :label="$t('workflow.steps.arriveWarehouse')"
        />
        <WorkflowStep
          :completed="prepareStatus !== null && prepareStatus >= 3"
          :active="prepareStatus === 3"
          icon="✓"
          :label="$t('workflow.steps.warehouseReceived')"
        />
        <WorkflowStep
          :completed="prepareStatus !== null && prepareStatus >= 4"
          :active="prepareStatus === 4"
          icon="🚚"
          :label="$t('workflow.steps.warehouseShips')"
        />
        <WorkflowStep
          :completed="prepareStatus !== null && prepareStatus >= 6"
          :active="prepareStatus === 6"
          icon="✅"
          :label="$t('workflow.steps.delivered')"
        />
      </template>

      <!-- Workflow 4: Driver → User (1,1) -->
      <template v-else-if="deliveryType === 1 && shippingType === 1">
        <WorkflowStep
          :completed="prepareStatus !== null && prepareStatus >= 0"
          :active="prepareStatus === 0"
          icon="📦"
          :label="$t('workflow.steps.goodsReady')"
        />
        <WorkflowStep
          :completed="prepareStatus !== null && prepareStatus >= 1"
          :active="prepareStatus === 1"
          icon="🚗"
          :label="$t('workflow.steps.driverPickup')"
        />
        <WorkflowStep
          :completed="prepareStatus !== null && prepareStatus >= 5"
          :active="prepareStatus === 5"
          icon="✅"
          :label="$t('workflow.steps.deliveredToUser')"
        />
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import WorkflowStep from './WorkflowStep.vue';

const props = defineProps<{
  deliveryType: number;
  shippingType: number;
  prepareStatus: number | null;
}>();

const workflowLabel = computed(() => {
  const key = `${props.deliveryType},${props.shippingType}`;
  const workflows: Record<string, string> = {
    '0,0': 'Workflow 1: Merchant → Warehouse → User',
    '0,1': 'Workflow 2: Merchant → User',
    '1,0': 'Workflow 3: Driver → Warehouse → User',
    '1,1': 'Workflow 4: Driver → User'
  };
  return workflows[key] || 'Unknown Workflow';
});

const currentStatusLabel = computed(() => {
  const labels: Record<number | string, string> = {
    null: 'Pending Prepare',
    0: 'Prepared',
    1: 'Driver Pickup',
    2: 'Driver to Warehouse',
    3: 'Warehouse Received',
    4: 'Warehouse Shipped',
    5: 'Delivered',
    6: 'Complete'
  };
  return labels[props.prepareStatus as any] || 'Unknown';
});
</script>

<style scoped>
.workflow-timeline {
  padding: 1.5rem;
  background: white;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.timeline-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
}

.timeline-status {
  padding: 0.25rem 0.75rem;
  background: #eff6ff;
  color: #1e40af;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.timeline-steps {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  overflow-x: auto;
  padding: 0.5rem 0;
}

@media (max-width: 768px) {
  .timeline-steps {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
