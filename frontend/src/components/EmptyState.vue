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
  background: #ffffff;
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  color: #64748b;
  border: 1px dashed #cbd5f5;
}
</style>
