import client from './client';

export interface PrepareGoodsItemDto {
  prepareId: number;
  orderItemId: number;
  productId: number;
  skuId: number;
  quantity: number;
}

export interface PrepareGoodsDto {
  id: number;
  prepareSn: string;
  orderIds: string;
  deliveryType: number;  // 0=Merchant, 1=Third-party driver
  shippingType: number;  // 0=To warehouse, 1=To user
  prepareStatus: number | null;  // null=pending, 0-6=workflow stages
  shopId: number;
  warehouseId: number | null;
  driverId: number | null;
  createTime: string;
  updateTime: string | null;
}

export interface PrepareGoodsDetailDto extends PrepareGoodsDto {
  items: PrepareGoodsItemDto[];
  warehouseName: string | null;
  driverName: string | null;
}

export interface PrepareGoodsSummaryDto {
  prepareSn: string;
  orderCount: number;
  deliveryType: number;
  shippingType: number;
  prepareStatus: number | null;
  prepareStatusLabel: string;
  warehouseName: string | null;
  driverName: string | null;
  createTime: string;
}

export interface CreatePreparePackageRequest {
  orderIds: number[];
  shopId: number;
  deliveryType: number;
  shippingType: number;
  warehouseId?: number | null;
}

export interface UpdatePrepareStatusRequest {
  newStatus: number;
}

export interface AssignDriverRequest {
  driverId: number;
}

/**
 * Create a new prepare goods package
 */
export async function createPreparePackage(request: CreatePreparePackageRequest) {
  const { data } = await client.post<PrepareGoodsDto>(
    '/prepare-goods',
    request
  );
  return data;
}

/**
 * Get prepare package by serial number
 */
export async function getPreparePackage(prepareSn: string) {
  const { data } = await client.get<PrepareGoodsDetailDto>(
    `/prepare-goods/${prepareSn}`
  );
  return data;
}

/**
 * Update prepare status
 */
export async function updatePrepareStatus(
  prepareSn: string,
  newStatus: number
) {
  await client.put(
    `/prepare-goods/${prepareSn}/status`,
    { newStatus } as UpdatePrepareStatusRequest
  );
}

/**
 * List prepare packages for a shop (merchant)
 */
export async function listShopPreparePackages(
  shopId: number,
  status?: number | null,
  limit: number = 50
) {
  const params: any = { limit };
  if (status !== null && status !== undefined) {
    params.status = status;
  }

  const { data } = await client.get<PrepareGoodsSummaryDto[]>(
    `/prepare-goods/shop/${shopId}`,
    { params }
  );
  return data;
}

/**
 * Assign a driver to a prepare package
 */
export async function assignDriver(prepareSn: string, driverId: number) {
  await client.post(
    `/prepare-goods/${prepareSn}/assign-driver`,
    { driverId } as AssignDriverRequest
  );
}

/**
 * List available packages ready for driver pickup
 * (unassigned packages with prepare_status = 0)
 */
export async function listAvailablePreparePackages(limit: number = 50) {
  const { data } = await client.get<PrepareGoodsSummaryDto[]>(
    '/prepare-goods/available',
    { params: { limit } }
  );
  return data;
}

/**
 * List prepare packages assigned to a driver
 */
export async function listDriverPreparePackages(
  driverId: number,
  limit: number = 50
) {
  const { data } = await client.get<PrepareGoodsSummaryDto[]>(
    `/prepare-goods/driver/${driverId}`,
    { params: { limit } }
  );
  return data;
}

/**
 * List prepare packages assigned to the current logged-in driver
 */
export async function listMyDriverPreparePackages(limit: number = 50) {
  const { data } = await client.get<PrepareGoodsSummaryDto[]>(
    '/prepare-goods/driver/me',
    { params: { limit } }
  );
  return data;
}

/**
 * Driver picks up a package
 */
export async function pickupPackage(prepareSn: string) {
  await client.post(`/prepare-goods/${prepareSn}/pickup`);
}
