<template>
  <div
    class="flex flex-col items-center p-6 bg-white shadow-lg rounded-lg w-96 mx-auto"
  >
    <h2 class="text-2xl font-bold mb-4">
      {{ isLogin ? 'Login' : 'Register' }}
    </h2>

    <!-- Error Message -->
    <div
      v-if="errorMessage"
      class="w-full mb-4 p-3 bg-red-100 text-red-700 rounded"
    >
      {{ errorMessage }}
    </div>

    <form @submit.prevent="handleSubmit" class="w-full flex flex-col gap-4">
      <InputText
        v-if="!isLogin"
        v-model="username"
        placeholder="Username"
        class="p-inputtext w-full"
        autocomplete="username"
        :class="{ 'p-invalid': formErrors.username }"
      />
      <small v-if="!isLogin && formErrors.username" class="text-red-500">{{
        formErrors.username
      }}</small>

      <InputText
        v-if="!isLogin"
        v-model="email"
        type="email"
        placeholder="Email"
        class="p-inputtext w-full"
        autocomplete="email"
        :class="{ 'p-invalid': formErrors.email }"
      />
      <small v-if="!isLogin && formErrors.email" class="text-red-500">{{
        formErrors.email
      }}</small>

      <InputText
        v-if="isLogin"
        v-model="identifier"
        placeholder="Email or Username"
        class="p-inputtext w-full"
        autocomplete="username"
        :class="{ 'p-invalid': formErrors.identifier }"
      />
      <small v-if="isLogin && formErrors.identifier" class="text-red-500">{{
        formErrors.identifier
      }}</small>

      <Password
        v-model="password"
        placeholder="Password"
        class="w-full"
        toggleMask
        :autocomplete="isLogin ? 'current-password' : 'new-password'"
        :feedback="!isLogin"
        :class="{ 'p-invalid': formErrors.password }"
      />
      <small v-if="formErrors.password" class="text-red-500">{{
        formErrors.password
      }}</small>

      <FileUpload
        v-if="!isLogin"
        mode="basic"
        auto
        chooseLabel="Choose Profile Picture"
        @select="handleFileUpload"
      />

      <Button
        type="submit"
        :label="isLogin ? 'Login' : 'Register'"
        class="w-full"
        :loading="loading"
      />
      <Button
        type="button"
        :label="
          isLogin ? 'Need an account? Register' : 'Have an account? Login'
        "
        class="w-full p-button-text"
        @click="toggleMode"
        :disabled="loading"
      />
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/users'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import FileUpload from 'primevue/fileupload'

const router = useRouter()
const userStore = useUserStore()

const isLogin = ref(true)
const username = ref('')
const email = ref('')
const identifier = ref('')
const password = ref('')
const profilePic = ref<File | null>(null)
const loading = ref(false)
const errorMessage = ref('')

interface FormErrors {
  username?: string
  email?: string
  identifier?: string
  password?: string
}

const formErrors = ref<FormErrors>({})

const validateForm = (): boolean => {
  formErrors.value = {}

  if (isLogin.value) {
    if (!identifier.value.trim()) {
      formErrors.value.identifier = 'Email or username is required'
    }
  } else {
    if (!username.value.trim()) {
      formErrors.value.username = 'Username is required'
    }
    if (!email.value.trim()) {
      formErrors.value.email = 'Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
      formErrors.value.email = 'Invalid email format'
    }
  }

  if (!password.value) {
    formErrors.value.password = 'Password is required'
  } else if (!isLogin.value && password.value.length < 8) {
    formErrors.value.password = 'Password must be at least 8 characters'
  }

  return Object.keys(formErrors.value).length === 0
}

const toggleMode = () => {
  isLogin.value = !isLogin.value
  username.value = ''
  email.value = ''
  identifier.value = ''
  password.value = ''
  profilePic.value = null
  errorMessage.value = ''
  formErrors.value = {}
}

const handleFileUpload = (event: any) => {
  profilePic.value = event.files[0]
}

const handleSubmit = async () => {
  if (!validateForm()) return

  loading.value = true
  errorMessage.value = ''

  try {
    if (isLogin.value) {
      await userStore.login(identifier.value, password.value)
    } else {
      await userStore.register(
        username.value,
        email.value,
        password.value,
        profilePic.value
      )
      // Show success message and switch to login
      errorMessage.value = 'Registration successful! Please login.'
      isLogin.value = true
    }
  } catch (error: any) {
    errorMessage.value = error?.error || 'An unexpected error occurred'
  } finally {
    loading.value = false
  }
}
</script>
