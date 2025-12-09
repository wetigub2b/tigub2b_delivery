import { defineStore } from 'pinia';
import {
  assignDriver,
  confirmDelivery,
  confirmPickup,
  createPreparePackage,
  getPreparePackage,
  listAvailablePreparePackages,
  listDriverPreparePackages,
  listMyDriverPreparePackages,
  listShopPreparePackages,
  pickupPackage,
  updatePrepareStatus,
  type CreatePreparePackageRequest,
  type PrepareGoodsDetailDto,
  type PrepareGoodsSummaryDto
} from '@/api/prepareGoods';
import { parseI18nJson } from '@/utils/i18n';
import { getCurrentLocale } from '@/i18n';

// Prepare status labels
const prepareStatusLabels: Record<number | string, string> = {
  null: 'Pending Prepare',
  0: 'Prepared',
  1: 'Driver Pickup In Progress',
  2: 'Delivered to Warehouse',
  3: 'Delivered Complete',
  4: 'Warehouse Shipped',
  5: 'Delivered',
  6: 'Driver Claimed'
};

// Delivery type labels
const deliveryTypeLabels: Record<number, string> = {
  0: 'Merchant Self-Delivery',
  1: 'Third-Party Driver'
};

// Shipping type labels
const shippingTypeLabels: Record<number, string> = {
  0: 'To Warehouse',
  1: 'To User'
};

// Workflow labels
function getWorkflowLabel(deliveryType: number, shippingType: number, prepareStatus?: number | null, pickupType?: string): string {
  // Workflow 5: Warehouse → User (second leg delivery)
  // This is when prepare_status=5 and the package is ready for pickup from warehouse
  if (pickupType === 'warehouse' || (prepareStatus === 5 && shippingType === 1)) {
    return 'Workflow 5: Warehouse → User';
  }

  const key = `${deliveryType},${shippingType}`;
  const workflows: Record<string, string> = {
    '0,0': 'Workflow 1: Merchant → Warehouse → User',
    '0,1': 'Workflow 2: Merchant → User',
    '1,0': 'Workflow 3: Driver → User',
    '1,1': 'Workflow 4: Driver → Warehouse → User'
  };
  return workflows[key] || 'Unknown Workflow';
}

export interface PrepareGoodsPackage extends PrepareGoodsSummaryDto {
  deliveryTypeLabel: string;
  shippingTypeLabel: string;
  workflowLabel: string;
}

export interface PrepareGoodsDetail extends PrepareGoodsDetailDto {
  deliveryTypeLabel: string;
  shippingTypeLabel: string;
  workflowLabel: string;
}

function decorateSummary(pkg: PrepareGoodsSummaryDto): PrepareGoodsPackage {
  const currentLocale = getCurrentLocale();
  return {
    ...pkg,
    prepareStatusLabel:
      pkg.prepareStatusLabel || prepareStatusLabels[pkg.prepareStatus as any] || 'Unknown',
    deliveryTypeLabel: deliveryTypeLabels[pkg.deliveryType] || 'Unknown',
    shippingTypeLabel: shippingTypeLabels[pkg.shippingType] || 'Unknown',
    workflowLabel: getWorkflowLabel(pkg.deliveryType, pkg.shippingType, pkg.prepareStatus, pkg.pickupType),
    warehouseName: parseI18nJson(pkg.warehouseName, currentLocale),
    driverName: parseI18nJson(pkg.driverName, currentLocale)
  };
}

function decorateDetail(detail: PrepareGoodsDetailDto): PrepareGoodsDetail {
  const currentLocale = getCurrentLocale();
  return {
    ...detail,
    deliveryTypeLabel: deliveryTypeLabels[detail.deliveryType] || 'Unknown',
    shippingTypeLabel: shippingTypeLabels[detail.shippingType] || 'Unknown',
    workflowLabel: getWorkflowLabel(detail.deliveryType, detail.shippingType, detail.prepareStatus),
    warehouseName: parseI18nJson(detail.warehouseName, currentLocale),
    driverName: parseI18nJson(detail.driverName, currentLocale)
  };
}

export const usePrepareGoodsStore = defineStore('prepareGoods', {
  state: () => ({
    // Merchant's packages
    shopPackages: [] as PrepareGoodsPackage[],

    // Driver's assigned packages
    driverPackages: [] as PrepareGoodsPackage[],

    // Available packages (unassigned, ready for pickup)
    availablePackages: [] as PrepareGoodsPackage[],

    // Currently viewed package detail
    currentPackage: null as PrepareGoodsDetail | null,

    // Loading states
    isLoading: false,
    isCreating: false,
    isUpdating: false
  }),

  getters: {
    packageBySn: (state) => (prepareSn: string) =>
      state.shopPackages.find((pkg) => pkg.prepareSn === prepareSn) ||
      state.driverPackages.find((pkg) => pkg.prepareSn === prepareSn),

    packagesByStatus: (state) => (status: number | null) => {
      const packages = [...state.shopPackages, ...state.driverPackages];
      if (status === null) {
        return packages.filter((pkg) => pkg.prepareStatus === null);
      }
      return packages.filter((pkg) => pkg.prepareStatus === status);
    },

    packagesByWorkflow: (state) => (deliveryType: number, shippingType: number) => {
      const packages = [...state.shopPackages, ...state.driverPackages];
      return packages.filter(
        (pkg) => pkg.deliveryType === deliveryType && pkg.shippingType === shippingType
      );
    }
  },

  actions: {
    /**
     * Create a new prepare goods package (Merchant action)
     */
    async createPackage(request: CreatePreparePackageRequest) {
      this.isCreating = true;
      try {
        const result = await createPreparePackage(request);

        // Add to shop packages list
        const summary: PrepareGoodsSummaryDto = {
          prepareSn: result.prepareSn,
          orderCount: request.orderIds.length,
          deliveryType: result.deliveryType,
          shippingType: result.shippingType,
          prepareStatus: result.prepareStatus,
          prepareStatusLabel: prepareStatusLabels[result.prepareStatus as any] || 'Unknown',
          warehouseName: null,
          driverName: null,
          createTime: result.createTime
        };

        this.shopPackages.unshift(decorateSummary(summary));

        return result;
      } finally {
        this.isCreating = false;
      }
    },

    /**
     * Get package detail by serial number
     */
    async fetchPackageDetail(prepareSn: string) {
      this.isLoading = true;
      try {
        const detail = await getPreparePackage(prepareSn);
        this.currentPackage = decorateDetail(detail);
        return this.currentPackage;
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * Update prepare status (Merchant/Driver/Warehouse action)
     */
    async updateStatus(prepareSn: string, newStatus: number) {
      this.isUpdating = true;
      try {
        await updatePrepareStatus(prepareSn, newStatus);

        // Update local state
        const shopPkg = this.shopPackages.find((pkg) => pkg.prepareSn === prepareSn);
        if (shopPkg) {
          shopPkg.prepareStatus = newStatus;
          shopPkg.prepareStatusLabel = prepareStatusLabels[newStatus] || 'Unknown';
        }

        const driverPkg = this.driverPackages.find((pkg) => pkg.prepareSn === prepareSn);
        if (driverPkg) {
          driverPkg.prepareStatus = newStatus;
          driverPkg.prepareStatusLabel = prepareStatusLabels[newStatus] || 'Unknown';
        }

        if (this.currentPackage?.prepareSn === prepareSn) {
          this.currentPackage.prepareStatus = newStatus;
        }
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * Fetch merchant's prepare packages
     */
    async fetchShopPackages(shopId: number, status?: number | null) {
      this.isLoading = true;
      try {
        const packages = await listShopPreparePackages(shopId, status);
        this.shopPackages = packages.map((pkg) => decorateSummary(pkg));
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * Assign driver to package (Merchant/Admin action)
     */
    async assignDriverToPackage(prepareSn: string, driverId: number) {
      this.isUpdating = true;
      try {
        await assignDriver(prepareSn, driverId);

        // Update local state
        const pkg = this.shopPackages.find((pkg) => pkg.prepareSn === prepareSn);
        if (pkg) {
          // Note: Driver name not immediately available, will be loaded on next fetch
          pkg.driverId = driverId;
        }

        if (this.currentPackage?.prepareSn === prepareSn) {
          this.currentPackage.driverId = driverId;
        }
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * Fetch driver's assigned packages (by driver ID)
     */
    async fetchDriverPackages(driverId: number) {
      this.isLoading = true;
      try {
        const packages = await listDriverPreparePackages(driverId);
        this.driverPackages = packages.map((pkg) => decorateSummary(pkg));
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * Fetch current logged-in driver's assigned packages
     */
    async fetchMyDriverPackages() {
      this.isLoading = true;
      try {
        const packages = await listMyDriverPreparePackages();
        this.driverPackages = packages.map((pkg) => decorateSummary(pkg));
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * Fetch available packages (unassigned, ready for pickup)
     */
    async fetchAvailablePackages() {
      this.isLoading = true;
      try {
        const packages = await listAvailablePreparePackages();
        this.availablePackages = packages.map((pkg) => decorateSummary(pkg));
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * Driver picks up a package
     */
    async pickupPackage(prepareSn: string) {
      this.isUpdating = true;
      try {
        await pickupPackage(prepareSn);

        // Remove from available packages
        this.availablePackages = this.availablePackages.filter(
          (pkg) => pkg.prepareSn !== prepareSn
        );

        // Refresh driver packages to show the newly picked up package
        await this.fetchMyDriverPackages();
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * Confirm pickup with photo proof
     */
    async confirmPickupWithProof(prepareSn: string, photo: string, notes?: string) {
      this.isUpdating = true;
      try {
        await confirmPickup(prepareSn, photo, notes);

        // Update local state - package moves from status 6 to status 1
        const pkg = this.driverPackages.find((pkg) => pkg.prepareSn === prepareSn);
        if (pkg) {
          pkg.prepareStatus = 1;
          pkg.prepareStatusLabel = prepareStatusLabels[1] || 'Unknown';
        }

        // Refresh driver packages to get updated state
        await this.fetchMyDriverPackages();
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * Confirm delivery with photo proof
     */
    async confirmDeliveryWithProof(prepareSn: string, photo: string, notes?: string) {
      this.isUpdating = true;
      try {
        await confirmDelivery(prepareSn, photo, notes);

        // Update local state - package status changes based on shipping type
        const pkg = this.driverPackages.find((pkg) => pkg.prepareSn === prepareSn);
        if (pkg) {
          // shipping_type = 0 (Workflow 3): user → status 3 (已送达)
          // shipping_type = 1 (Workflow 4): warehouse → status 2 (司机送达仓库)
          const newStatus = pkg.shippingType === 1 ? 2 : 3;
          pkg.prepareStatus = newStatus;
          pkg.prepareStatusLabel = prepareStatusLabels[newStatus] || 'Unknown';
        }

        // Refresh driver packages to get updated state
        await this.fetchMyDriverPackages();
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * Clear current package detail
     */
    clearCurrentPackage() {
      this.currentPackage = null;
    }
  }
});
