<template>
  <div class="empty">
    <p>{{ message }}</p>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue';

defineProps<{ message: string }>();
</script>

<style scoped>
.empty {
  background: var(--color-white);
  border-radius: var(--radius-md);
  padding: var(--spacing-2xl);
  text-align: center;
  color: var(--color-text-secondary);
  border: 1px dashed var(--color-gray-light);
}
</style>
