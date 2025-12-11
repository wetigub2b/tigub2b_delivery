<template>
  <div class="prepare-goods-list">
    <div class="page-header">
      <h1 class="page-title">{{ $t('prepareGoods.packageList') }}</h1>
      <button class="create-button" @click="goToCreate">
        + {{ $t('prepareGoods.createPackage') }}
      </button>
    </div>

    <!-- Filters -->
    <div class="filters-bar">
      <select v-model="statusFilter" class="status-filter" @change="loadPackages">
        <option :value="null">{{ $t('prepareGoods.allStatuses') }}</option>
        <option :value="0">{{ $t('prepareGoods.status.prepared') }}</option>
        <option :value="1">{{ $t('prepareGoods.status.driverPickup') }}</option>
        <option :value="2">{{ $t('prepareGoods.status.driverToWarehouse') }}</option>
        <option :value="3">{{ $t('prepareGoods.status.warehouseReceived') }}</option>
        <option :value="4">{{ $t('prepareGoods.status.warehouseShipped') }}</option>
        <option :value="5">{{ $t('prepareGoods.status.delivered') }}</option>
        <option :value="6">{{ $t('prepareGoods.status.complete') }}</option>
      </select>

      <button class="refresh-button" @click="loadPackages" :disabled="isLoading">
        🔄 {{ $t('common.refresh') }}
      </button>
    </div>

    <!-- Packages list -->
    <div class="packages-container">
      <div v-if="isLoading" class="loading-state">
        {{ $t('common.loading') }}...
      </div>

      <div v-else-if="packages.length === 0" class="empty-state">
        <p>{{ $t('prepareGoods.noPackages') }}</p>
        <button class="create-button-large" @click="goToCreate">
          {{ $t('prepareGoods.createFirstPackage') }}
        </button>
      </div>

      <div v-else class="packages-grid">
        <div
          v-for="pkg in packages"
          :key="pkg.prepareSn"
          class="package-card"
          @click="viewPackageDetail(pkg.prepareSn)"
        >
          <div class="card-header">
            <span class="package-sn">{{ pkg.prepareSn }}</span>
            <span class="package-status" :class="`status-${pkg.prepareStatus}`">
              {{ pkg.prepareStatusLabel }}
            </span>
          </div>

          <div class="card-body">
            <div class="package-info">
              <div class="info-row">
                <span class="info-label">{{ $t('taskBoard.workflow') }}:</span>
                <span class="info-value">{{ $t(pkg.workflowLabel) }}</span>
              </div>

              <div class="info-row">
                <span class="info-label">{{ $t('prepareGoods.ordersCount') }}:</span>
                <span class="info-value">{{ pkg.orderCount }} {{ $t('prepareGoods.orders') }}</span>
              </div>

              <div v-if="pkg.warehouseName" class="info-row">
                <span class="info-label">{{ $t('prepareGoods.warehouse') }}:</span>
                <span class="info-value">{{ pkg.warehouseName }}</span>
              </div>

              <div v-if="pkg.driverName" class="info-row">
                <span class="info-label">{{ $t('prepareGoods.driver') }}:</span>
                <span class="info-value">{{ pkg.driverName }}</span>
              </div>

              <div class="info-row">
                <span class="info-label">{{ $t('prepareGoods.createTime') }}:</span>
                <span class="info-value">{{ formatDate(pkg.createTime) }}</span>
              </div>
            </div>
          </div>

          <div class="card-footer">
            <button class="view-button" @click.stop="viewPackageDetail(pkg.prepareSn)">
              {{ $t('common.viewDetails') }} →
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { usePrepareGoodsStore } from '@/store/prepareGoods';

const router = useRouter();
const prepareGoodsStore = usePrepareGoodsStore();

const statusFilter = ref<number | null>(null);
const isLoading = ref(false);
const shopId = ref(1); // TODO: Get from auth store

const packages = ref(prepareGoodsStore.shopPackages);

async function loadPackages() {
  isLoading.value = true;
  try {
    await prepareGoodsStore.fetchShopPackages(shopId.value, statusFilter.value);
    packages.value = prepareGoodsStore.shopPackages;
  } finally {
    isLoading.value = false;
  }
}

function goToCreate() {
  router.push({ name: 'PrepareGoodsCreate' });
}

function viewPackageDetail(prepareSn: string) {
  router.push({ name: 'PrepareGoodsDetail', params: { prepareSn } });
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString();
}

onMounted(() => {
  loadPackages();
});
</script>

<style scoped>
.prepare-goods-list {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1.5rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.page-title {
  font-size: 1.875rem;
  font-weight: 700;
  color: #1f2937;
}

.create-button {
  padding: 0.75rem 1.5rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;
}

.create-button:hover {
  background: #2563eb;
}

.filters-bar {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.status-filter {
  padding: 0.5rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  background: white;
}

.refresh-button {
  padding: 0.5rem 1rem;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;
}

.refresh-button:hover:not(:disabled) {
  background: #f3f4f6;
}

.refresh-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.packages-container {
  min-height: 400px;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  text-align: center;
  color: #6b7280;
}

.create-button-large {
  margin-top: 1.5rem;
  padding: 0.75rem 2rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  font-size: 1rem;
}

.create-button-large:hover {
  background: #2563eb;
}

.packages-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.package-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.package-card:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
  border-color: #3b82f6;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.package-sn {
  font-weight: 600;
  color: #1f2937;
  font-size: 1rem;
}

.package-status {
  padding: 0.25rem 0.75rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-0 {
  background: #fef3c7;
  color: #92400e;
}

.status-1,
.status-2 {
  background: #dbeafe;
  color: #1e40af;
}

.status-3,
.status-4 {
  background: #e0e7ff;
  color: #3730a3;
}

.status-5 {
  background: #d1fae5;
  color: #065f46;
}

.status-6 {
  background: #d1fae5;
  color: #047857;
}

.card-body {
  margin-bottom: 1rem;
}

.package-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
}

.info-label {
  color: #6b7280;
  font-weight: 500;
}

.info-value {
  color: #1f2937;
  font-weight: 600;
  text-align: right;
}

.card-footer {
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.view-button {
  width: 100%;
  padding: 0.5rem;
  background: #eff6ff;
  color: #2563eb;
  border: 1px solid #dbeafe;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;
}

.view-button:hover {
  background: #dbeafe;
}

@media (max-width: 768px) {
  .packages-grid {
    grid-template-columns: 1fr;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }

  .filters-bar {
    flex-direction: column;
  }
}
</style>
