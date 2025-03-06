<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  modelValue: string
  id?: string
  placeholder?: string
  disabled?: boolean
  label?: string
  error?: string
  autocomplete?: string
}>()

const emit = defineEmits(['update:modelValue'])

const showPassword = ref(false)

const togglePasswordVisibility = () => {
  showPassword.value = !showPassword.value
}

const updateValue = (event: Event) => {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}
</script>

<template>
  <div class="password-field">
    <label v-if="label" :for="id" class="password-label">{{ label }}</label>
    <div class="password-input-wrapper">
      <input
        :id="id"
        :type="showPassword ? 'text' : 'password'"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :autocomplete="autocomplete || 'current-password'"
        @input="updateValue"
        class="password-input"
      />
      <button
        type="button"
        @click="togglePasswordVisibility"
        class="toggle-password-btn"
        :aria-label="showPassword ? 'Hide password' : 'Show password'"
        tabindex="-1"
      >
        <!-- Show password icon (eye) -->
        <svg
          v-if="!showPassword"
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="eye-icon"
        >
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
          <circle cx="12" cy="12" r="3"></circle>
        </svg>

        <!-- Hide password icon (eye with slash) -->
        <svg
          v-else
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="eye-icon"
        >
          <path
            d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"
          ></path>
          <line x1="1" y1="1" x2="23" y2="23"></line>
        </svg>
      </button>
    </div>
    <p v-if="error" class="error-text">{{ error }}</p>
  </div>
</template>

<style lang="scss" scoped>
.password-field {
  margin-bottom: 16px;
  width: 100%;
}

.password-label {
  display: block;
  margin-bottom: 8px;
  color: #333;
  font-weight: 500;
}

.password-input-wrapper {
  position: relative;
  display: flex;
}

.password-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 16px;
  transition: border-color 0.2s;
}

.password-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
}

.password-input:disabled {
  background-color: #f8f9fa;
  cursor: not-allowed;
}

.toggle-password-btn {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6c757d;
}

.toggle-password-btn:hover {
  color: #495057;
}

.eye-icon {
  color: #6c757d;
}

.error-text {
  color: #dc3545;
  font-size: 0.875rem;
  margin-top: 0.5rem;
  margin-bottom: 0;
}
</style>
