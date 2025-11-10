<template>
  <div class="workflow-step" :class="{ completed, active, pending: !completed && !active }">
    <div class="step-icon">
      {{ icon }}
    </div>
    <div class="step-label">
      {{ label }}
    </div>
    <div v-if="!isLast" class="step-connector" :class="{ completed }"></div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  icon: string;
  label: string;
  completed: boolean;
  active: boolean;
  isLast?: boolean;
}>();
</script>

<style scoped>
.workflow-step {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  min-width: 120px;
}

.step-icon {
  width: 3rem;
  height: 3rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  background: #f3f4f6;
  border: 2px solid #d1d5db;
  transition: all 0.3s;
  z-index: 1;
}

.workflow-step.completed .step-icon {
  background: #10b981;
  border-color: #10b981;
  box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.1);
}

.workflow-step.active .step-icon {
  background: #3b82f6;
  border-color: #3b82f6;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2);
  animation: pulse 2s infinite;
}

.workflow-step.pending .step-icon {
  background: #f3f4f6;
  border-color: #d1d5db;
  opacity: 0.6;
}

.step-label {
  margin-top: 0.5rem;
  font-size: 0.75rem;
  font-weight: 500;
  color: #6b7280;
  text-align: center;
  max-width: 120px;
}

.workflow-step.completed .step-label {
  color: #059669;
  font-weight: 600;
}

.workflow-step.active .step-label {
  color: #2563eb;
  font-weight: 600;
}

.step-connector {
  position: absolute;
  top: 1.5rem;
  left: 50%;
  right: -50%;
  height: 2px;
  background: #d1d5db;
  z-index: 0;
}

.step-connector.completed {
  background: #10b981;
}

@keyframes pulse {
  0%,
  100% {
    box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(59, 130, 246, 0.1);
  }
}

@media (max-width: 768px) {
  .workflow-step {
    flex-direction: row;
    min-width: unset;
    width: 100%;
    padding: 0.75rem;
    background: #f9fafb;
    border-radius: 0.375rem;
    margin-bottom: 0.5rem;
  }

  .step-icon {
    width: 2.5rem;
    height: 2.5rem;
    font-size: 1.25rem;
  }

  .step-label {
    margin-top: 0;
    margin-left: 0.75rem;
    text-align: left;
    flex: 1;
  }

  .step-connector {
    display: none;
  }
}
</style>
