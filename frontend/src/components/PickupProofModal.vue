<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="show" class="modal-overlay" @click="handleCancel">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3>{{ $t('taskBoard.pickupProof') }}</h3>
            <button class="modal-close" @click="handleCancel" aria-label="Close">
              ✕
            </button>
          </div>

          <div class="modal-body">
            <div class="package-summary">
              <div class="summary-row">
                <span class="summary-label">{{ $t('packageModal.packageNumber') }}:</span>
                <span class="summary-value">{{ packageData.prepareSn }}</span>
              </div>
              <div class="summary-row">
                <span class="summary-label">{{ $t('packageModal.totalOrders') }}:</span>
                <span class="summary-value">{{ packageData.orderCount }}</span>
              </div>
              <div v-if="packageData.workflowLabel" class="summary-row">
                <span class="summary-label">{{ $t('taskBoard.workflow') }}:</span>
                <span class="summary-value">{{ packageData.workflowLabel }}</span>
              </div>
              <div v-if="packageData.warehouseName" class="summary-row">
                <span class="summary-label">{{ $t('taskBoard.warehouse') }}:</span>
                <span class="summary-value">{{ packageData.warehouseName }}</span>
              </div>
            </div>

            <div class="photo-section">
              <div v-if="photoPreview" class="photo-preview">
                <img :src="photoPreview" alt="Pickup proof" />
                <button class="photo-retake" @click="clearPhoto">
                  {{ $t('orderCard.retakePhoto') }}
                </button>
              </div>
              <div v-else class="photo-actions">
                <button class="photo-button photo-button--camera" @click="takePhoto" :disabled="isProcessing">
                  <span class="photo-icon">📷</span>
                  {{ $t('orderCard.takePhoto') }}
                </button>
                <button class="photo-button photo-button--upload" @click="uploadPhoto" :disabled="isProcessing">
                  <span class="photo-icon">🖼️</span>
                  {{ $t('orderCard.uploadPhoto') }}
                </button>
              </div>
              <p v-if="photoError" class="error-message">{{ photoError }}</p>
            </div>

            <div class="notes-section">
              <label for="pickup-notes">{{ $t('taskBoard.pickupNotes') }}</label>
              <textarea
                id="pickup-notes"
                v-model="notes"
                :placeholder="$t('taskBoard.pickupNotesPlaceholder')"
                rows="3"
                maxlength="500"
              ></textarea>
              <span class="char-count">{{ notes.length }}/500</span>
            </div>
          </div>

          <div class="modal-footer">
            <button class="modal-button modal-button--cancel" @click="handleCancel" :disabled="isProcessing">
              {{ $t('common.cancel') }}
            </button>
            <button
              class="modal-button modal-button--confirm"
              @click="handleSubmit"
              :disabled="!photoPreview || isProcessing"
            >
              {{ isProcessing ? $t('common.loading') : $t('taskBoard.submitPickup') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';
import { Capacitor } from '@capacitor/core';

interface PackageData {
  prepareSn: string;
  orderCount: number;
  workflowLabel?: string;
  warehouseName?: string;
}

const props = defineProps<{
  show: boolean;
  packageData: PackageData;
}>();

const emit = defineEmits<{
  submit: [photo: string, notes: string];
  cancel: [];
}>();

const photoPreview = ref<string>('');
const notes = ref('');
const photoError = ref('');
const isProcessing = ref(false);

const isWeb = Capacitor.getPlatform() === 'web';

async function takePhoto() {
  if (isWeb) {
    // Web fallback - use file input with camera
    triggerFileInput(true);
    return;
  }

  try {
    photoError.value = '';

    // Request camera permissions
    const permissions = await Camera.requestPermissions();
    if (permissions.camera !== 'granted') {
      photoError.value = 'Camera permission denied';
      return;
    }

    // Take photo
    const photo = await Camera.getPhoto({
      quality: 80,
      allowEditing: false,
      resultType: CameraResultType.DataUrl,
      source: CameraSource.Camera,
      width: 1920,
      height: 1080,
      correctOrientation: true
    });

    if (photo.dataUrl) {
      validateAndSetPhoto(photo.dataUrl);
    }
  } catch (error) {
    console.error('Camera error:', error);
    photoError.value = 'Failed to take photo';
  }
}

async function uploadPhoto() {
  if (isWeb) {
    // Web fallback - use file input
    triggerFileInput(false);
    return;
  }

  try {
    photoError.value = '';

    // Request photos permissions
    const permissions = await Camera.requestPermissions();
    if (permissions.photos !== 'granted') {
      photoError.value = 'Photo library permission denied';
      return;
    }

    // Select photo from gallery
    const photo = await Camera.getPhoto({
      quality: 80,
      allowEditing: false,
      resultType: CameraResultType.DataUrl,
      source: CameraSource.Photos,
      width: 1920,
      height: 1080
    });

    if (photo.dataUrl) {
      validateAndSetPhoto(photo.dataUrl);
    }
  } catch (error) {
    console.error('Upload error:', error);
    photoError.value = 'Failed to upload photo';
  }
}

function triggerFileInput(useCamera: boolean) {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/jpeg,image/jpg,image/png';
  if (useCamera) {
    input.capture = 'environment';
  }

  input.onchange = (e) => {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  input.click();
}

function handleFileSelect(file: File) {
  photoError.value = '';

  // Validate file type
  if (!['image/jpeg', 'image/jpg', 'image/png'].includes(file.type)) {
    photoError.value = 'Only JPEG and PNG images are allowed';
    return;
  }

  // Validate file size
  const sizeMB = file.size / (1024 * 1024);
  if (sizeMB > 4) {
    photoError.value = `Photo size (${sizeMB.toFixed(1)}MB) exceeds 4MB limit`;
    return;
  }

  // Convert to base64
  const reader = new FileReader();
  reader.onload = (e) => {
    const dataUrl = e.target?.result as string;
    if (dataUrl) {
      photoPreview.value = dataUrl;
    }
  };
  reader.onerror = () => {
    photoError.value = 'Failed to read file';
  };
  reader.readAsDataURL(file);
}

function validateAndSetPhoto(dataUrl: string) {
  // Validate size
  const sizeBytes = Math.ceil(dataUrl.length * 0.75); // Approximate base64 size
  const sizeMB = sizeBytes / (1024 * 1024);

  if (sizeMB > 4) {
    photoError.value = `Photo size (${sizeMB.toFixed(1)}MB) exceeds 4MB limit`;
    return;
  }

  photoPreview.value = dataUrl;
}

function clearPhoto() {
  photoPreview.value = '';
  photoError.value = '';
}

function handleCancel() {
  if (!isProcessing.value) {
    clearPhoto();
    notes.value = '';
    emit('cancel');
  }
}

async function handleSubmit() {
  if (!photoPreview.value || isProcessing.value) return;

  isProcessing.value = true;
  try {
    emit('submit', photoPreview.value, notes.value);
  } catch (error) {
    photoError.value = 'Failed to submit pickup proof';
    isProcessing.value = false;
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: var(--spacing-md);
}

.modal-container {
  background: var(--color-white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg) var(--spacing-xl);
  border-bottom: 1px solid var(--color-gray-lighter);
}

.modal-header h3 {
  margin: 0;
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-dark);
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--color-gray);
  cursor: pointer;
  padding: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  transition: all var(--transition-base);
}

.modal-close:hover {
  background: var(--color-gray-lighter);
  color: var(--color-gray-dark);
}

.modal-body {
  padding: var(--spacing-xl);
  overflow-y: auto;
  flex: 1;
}

.package-summary {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-lg);
  border-bottom: 1px solid var(--color-gray-lighter);
}

.summary-row {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-md);
}

.summary-label {
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray);
}

.summary-value {
  color: var(--color-gray-dark);
  text-align: right;
}

.photo-section {
  margin-bottom: var(--spacing-lg);
}

.photo-preview {
  position: relative;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-gray-lightest);
}

.photo-preview img {
  width: 100%;
  height: auto;
  display: block;
}

.photo-retake {
  position: absolute;
  bottom: var(--spacing-md);
  right: var(--spacing-md);
  background: var(--color-white);
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
  padding: var(--spacing-sm) var(--spacing-lg);
  border-radius: var(--radius-full);
  cursor: pointer;
  font-weight: var(--font-weight-semibold);
  transition: all var(--transition-base);
}

.photo-retake:hover {
  background: var(--color-primary);
  color: var(--color-white);
}

.photo-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
}

.photo-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  border-radius: var(--radius-md);
  border: 2px dashed var(--color-gray-light);
  background: var(--color-gray-lightest);
  cursor: pointer;
  transition: all var(--transition-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-gray-dark);
}

.photo-button:hover:not(:disabled) {
  border-color: var(--color-primary);
  background: var(--color-white);
  color: var(--color-primary);
}

.photo-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.photo-icon {
  font-size: 2rem;
}

.error-message {
  color: var(--color-error, #ef4444);
  font-size: var(--font-size-sm);
  margin-top: var(--spacing-sm);
}

.notes-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.notes-section label {
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-dark);
}

.notes-section textarea {
  width: 100%;
  padding: var(--spacing-md);
  border: 1px solid var(--color-gray-light);
  border-radius: var(--radius-md);
  font-family: inherit;
  font-size: var(--font-size-md);
  resize: vertical;
  min-height: 80px;
}

.notes-section textarea:focus {
  outline: none;
  border-color: var(--color-primary);
}

.char-count {
  align-self: flex-end;
  font-size: var(--font-size-sm);
  color: var(--color-gray);
}

.modal-footer {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-lg) var(--spacing-xl);
  border-top: 1px solid var(--color-gray-lighter);
  background: var(--color-gray-lightest);
}

.modal-button {
  flex: 1;
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: var(--radius-full);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-base);
  border: none;
}

.modal-button--cancel {
  background: var(--color-white);
  color: var(--color-gray-dark);
  border: 1px solid var(--color-gray-light);
}

.modal-button--cancel:hover:not(:disabled) {
  background: var(--color-gray-lighter);
  border-color: var(--color-gray);
}

.modal-button--confirm {
  background: var(--color-primary);
  color: var(--color-white);
}

.modal-button--confirm:hover:not(:disabled) {
  background: var(--color-primary-dark);
  color: var(--color-white);
}

.modal-button--confirm:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Modal transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--transition-base);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform var(--transition-base);
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.9);
}

@media (max-width: 768px) {
  .modal-container {
    max-width: 100%;
    margin: var(--spacing-md);
  }

  .modal-footer {
    flex-direction: column-reverse;
  }

  .modal-button {
    width: 100%;
  }

  .photo-actions {
    grid-template-columns: 1fr;
  }
}
</style>
