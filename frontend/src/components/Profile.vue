<template>
  <div
    class="flex flex-col items-center p-6 bg-white shadow-lg rounded-lg w-96 mx-auto"
  >
    <h2 class="text-2xl font-bold mb-4">User Profile</h2>
    <div v-if="user" class="w-full flex flex-col gap-4 items-center">
      <p class="text-lg">Username: {{ user.username }}</p>
      <p class="text-lg">Email: {{ user.email }}</p>
      <img
        v-if="user.profile_pic"
        :src="profilePicUrl"
        class="rounded-full w-24 h-24"
        alt="Profile Picture"
      />
      <FileUpload
        mode="basic"
        auto
        chooseLabel="Choose New Profile Picture"
        @select="handleFileUpload"
      />
      <Button
        label="Upload Profile Picture"
        class="w-full"
        @click="uploadProfilePic"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/users'
import FileUpload from 'primevue/fileupload'
import Button from 'primevue/button'

const userStore = useUserStore()
const profilePic = ref<File | null>(null)

type User = {
  username: string
  email: string
  profile_pic: string | null
}

const user = computed<User | null>(() => userStore.user as User | null)

const profilePicUrl = computed(() => {
  return user.value?.profile_pic
    ? `https://wavegerpython.onrender.com/api/profile-pic/${user.value.profile_pic}`
    : ''
})

const handleFileUpload = (event: any) => {
  profilePic.value = event.files[0]
}

const uploadProfilePic = async () => {
  if (profilePic.value) {
    await userStore.uploadProfilePic(profilePic.value)
  }
}

onMounted(() => {
  userStore.fetchUserProfile()
})
</script>
