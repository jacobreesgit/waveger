<template>
  <div>
    <h2>User Profile</h2>
    <div v-if="userStore.user">
      <p>Username: {{ userStore.user.username }}</p>
      <p>Email: {{ userStore.user.email }}</p>
      <img
        v-if="userStore.user.profile_pic"
        :src="profilePicUrl"
        alt="Profile Picture"
      />
      <input type="file" @change="handleFileUpload" />
      <button @click="uploadProfilePic">Upload Profile Picture</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/users'

const userStore = useUserStore()
const profilePic = ref<File | null>(null)

const profilePicUrl = computed(() =>
  userStore.user?.profile_pic
    ? `https://wavegerpython.onrender.com/api/profile-pic/${userStore.user.profile_pic}`
    : ''
)

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files) {
    profilePic.value = target.files[0]
  }
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
