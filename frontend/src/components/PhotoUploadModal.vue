<template>
  <div class="modal-overlay" @click.self="$emit('cancel')">
    <div class="modal-content">
      <header class="modal-header">
        <h2>{{ title }}</h2>
        <button @click="$emit('cancel')" class="close-btn" aria-label="Close">×</button>
      </header>

      <div class="modal-body">
        <div class="photo-upload">
          <input
            type="file"
            accept="image/*"
            capture="environment"
            @change="handlePhotoSelect"
            ref="photoInput"
            style="display: none"
          />

          <div v-if="photoPreview" class="photo-preview">
            <img :src="photoPreview" alt="Preview" />
            <button @click="clearPhoto" class="btn-clear">
              {{ $t('photoUpload.retake') || 'Retake Photo' }}
            </button>
          </div>

          <button v-else @click="triggerFileInput" class="btn-camera">
            📷 {{ $t('photoUpload.takePhoto') || 'Take Photo' }}
          </button>
        </div>

        <div class="notes-input">
          <label for="notes">{{ $t('photoUpload.notes') || 'Notes' }} ({{ $t('photoUpload.optional') || 'optional' }})</label>
          <textarea
            id="notes"
            v-model="notes"
            :placeholder="$t('photoUpload.notesPlaceholder') || 'Add delivery notes...'"
            maxlength="1000"
            rows="4"
          />
          <span class="char-count">{{ notes.length }}/1000</span>
        </div>
      </div>

      <footer class="modal-actions">
        <button @click="$emit('cancel')" class="btn-secondary">
          {{ $t('photoUpload.cancel') || 'Cancel' }}
        </button>
        <button
          @click="handleSubmit"
          :disabled="!photoBase64 || isSubmitting"
          class="btn-primary"
        >
          {{ isSubmitting ? ($t('photoUpload.submitting') || 'Submitting...') : ($t('photoUpload.submit') || 'Submit') }}
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

defineProps<{
  title: string;
}>();

const emit = defineEmits<{
  submit: [photo: string, notes: string];
  cancel: [];
}>();

const photoInput = ref<HTMLInputElement | null>(null);
const photoBase64 = ref('');
const photoPreview = ref('');
const notes = ref('');
const isSubmitting = ref(false);

function triggerFileInput() {
  photoInput.value?.click();
}

function handlePhotoSelect(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;

  // Validate file size (max 4MB)
  if (file.size > 4 * 1024 * 1024) {
    alert('Photo size must be less than 4MB');
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    photoBase64.value = e.target?.result as string;
    photoPreview.value = photoBase64.value;
  };
  reader.readAsDataURL(file);
}

function clearPhoto() {
  photoBase64.value = '';
  photoPreview.value = '';
  if (photoInput.value) {
    photoInput.value.value = '';
  }
}

async function handleSubmit() {
  if (!photoBase64.value || isSubmitting.value) return;

  isSubmitting.value = true;
  try {
    emit('submit', photoBase64.value, notes.value);
  } finally {
    isSubmitting.value = false;
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
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--spacing-md);
}

.modal-content {
  background: var(--color-white);
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-xl);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-gray-lighter);
}

.modal-header h2 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-dark);
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 2rem;
  color: var(--color-gray);
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  transition: all var(--transition-base);
}

.close-btn:hover {
  background: var(--color-gray-lighter);
  color: var(--color-gray-dark);
}

.modal-body {
  padding: var(--spacing-lg);
  overflow-y: auto;
  flex: 1;
}

.photo-upload {
  margin-bottom: var(--spacing-lg);
}

.btn-camera {
  width: 100%;
  padding: var(--spacing-xl);
  border: 2px dashed var(--color-gray-light);
  background: var(--color-gray-lightest);
  color: var(--color-gray-dark);
  border-radius: var(--radius-md);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base);
}

.btn-camera:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-lightest);
  color: var(--color-primary);
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
  max-height: 300px;
  object-fit: contain;
}

.btn-clear {
  width: 100%;
  padding: var(--spacing-md);
  margin-top: var(--spacing-sm);
  border: 1px solid var(--color-gray-light);
  background: var(--color-white);
  color: var(--color-gray-dark);
  border-radius: var(--radius-md);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base);
}

.btn-clear:hover {
  border-color: var(--color-danger);
  color: var(--color-danger);
}

.notes-input {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.notes-input label {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  color: var(--color-gray-dark);
}

.notes-input textarea {
  width: 100%;
  padding: var(--spacing-md);
  border: 1px solid var(--color-gray-light);
  border-radius: var(--radius-md);
  font-size: var(--font-size-md);
  font-family: inherit;
  resize: vertical;
  min-height: 80px;
  transition: border-color var(--transition-base);
}

.notes-input textarea:focus {
  outline: none;
  border-color: var(--color-primary);
}

.char-count {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  text-align: right;
}

.modal-actions {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-gray-lighter);
}

.modal-actions button {
  flex: 1;
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: var(--radius-md);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base);
  border: none;
}

.btn-secondary {
  background: var(--color-white);
  color: var(--color-gray-dark);
  border: 1px solid var(--color-gray-light);
}

.btn-secondary:hover {
  background: var(--color-gray-lightest);
}

.btn-primary {
  background: var(--color-primary);
  color: var(--color-white);
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-dark);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .modal-overlay {
    padding: 0;
  }

  .modal-content {
    max-width: 100%;
    max-height: 100vh;
    border-radius: 0;
  }
}
</style>
