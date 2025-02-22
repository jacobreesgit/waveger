<template>
  <div
    class="flex flex-col items-center p-6 bg-white shadow-lg rounded-lg w-96 mx-auto"
  >
    <h2 class="text-2xl font-bold mb-4">
      {{ isLogin ? 'Login' : 'Register' }}
    </h2>
    <form @submit.prevent="handleSubmit" class="w-full flex flex-col gap-4">
      <InputText
        v-if="!isLogin"
        v-model="username"
        placeholder="Username"
        class="p-inputtext w-full"
        autocomplete="username"
      />
      <InputText
        v-model="email"
        type="email"
        placeholder="Email"
        class="p-inputtext w-full"
        autocomplete="email"
      />
      <Password
        v-model="password"
        placeholder="Password"
        class="p-inputtext w-full"
        toggleMask
        :autocomplete="isLogin ? 'current-password' : 'new-password'"
      />
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
      />
      <Button
        type="button"
        :label="
          isLogin ? 'Need an account? Register' : 'Have an account? Login'
        "
        class="w-full p-button-text"
        @click="toggleMode"
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
const password = ref('')
const profilePic = ref<File | null>(null)

const toggleMode = () => {
  isLogin.value = !isLogin.value
  username.value = ''
  email.value = ''
  password.value = ''
  profilePic.value = null
}

const handleFileUpload = (event: any) => {
  profilePic.value = event.files[0]
}

const handleSubmit = async () => {
  try {
    if (isLogin.value) {
      await userStore.login(email.value, password.value)
      console.log('Login successful:', { email: email.value })
    } else {
      await userStore.register(
        username.value,
        email.value,
        password.value,
        profilePic.value
      )
      console.log('Registration successful:', {
        username: username.value,
        email: email.value,
        hasProfilePic: !!profilePic.value,
      })
    }
    router.push('/profile')
  } catch (error) {
    console.error(`${isLogin.value ? 'Login' : 'Registration'} failed:`, error)
  }
}
</script>
