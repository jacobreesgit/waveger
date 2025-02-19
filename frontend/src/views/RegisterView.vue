<template>
  <div
    class="flex flex-col items-center p-6 bg-white shadow-lg rounded-lg w-96 mx-auto"
  >
    <h2 class="text-2xl font-bold mb-4">Register</h2>
    <form @submit.prevent="registerUser" class="w-full flex flex-col gap-4">
      <InputText
        v-model="username"
        placeholder="Username"
        class="p-inputtext w-full"
      />
      <InputText
        v-model="email"
        type="email"
        placeholder="Email"
        class="p-inputtext w-full"
      />
      <Password
        v-model="password"
        placeholder="Password"
        class="p-inputtext w-full"
        toggleMask
      />
      <FileUpload
        mode="basic"
        auto
        chooseLabel="Choose Profile Picture"
        @select="handleFileUpload"
      />
      <Button type="submit" label="Register" class="w-full" />
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useUserStore } from '@/stores/users'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import FileUpload from 'primevue/fileupload'

const userStore = useUserStore()
const username = ref('')
const email = ref('')
const password = ref('')
const profilePic = ref<File | null>(null)

const handleFileUpload = (event: any) => {
  profilePic.value = event.files[0]
}

const registerUser = async () => {
  await userStore.register(
    username.value,
    email.value,
    password.value,
    profilePic.value
  )
}
</script>
