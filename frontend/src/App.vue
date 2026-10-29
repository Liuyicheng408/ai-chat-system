<script setup>
import { onMounted } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
onMounted(() => {
  userStore.applyTheme()
})
</script>

<template>
  <router-view />
</template>
