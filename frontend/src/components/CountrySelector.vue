<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useTimezoneStore } from '@/stores/timezone'
import Dropdown from 'primevue/dropdown'

const timezoneStore = useTimezoneStore()

// Define country options with timezones
const countryOptions = [
  { code: 'US', name: 'United States', timezone: 'America/New_York' },
  { code: 'GB', name: 'United Kingdom', timezone: 'Europe/London' },
  { code: 'JP', name: 'Japan', timezone: 'Asia/Tokyo' },
  { code: 'AU', name: 'Australia', timezone: 'Australia/Sydney' },
  { code: 'DE', name: 'Germany', timezone: 'Europe/Berlin' },
  { code: 'FR', name: 'France', timezone: 'Europe/Paris' },
  { code: 'CA', name: 'Canada', timezone: 'America/Toronto' },
  { code: 'BR', name: 'Brazil', timezone: 'America/Sao_Paulo' },
  { code: 'IN', name: 'India', timezone: 'Asia/Kolkata' },
  { code: 'CN', name: 'China', timezone: 'Asia/Shanghai' },
  { code: 'ZA', name: 'South Africa', timezone: 'Africa/Johannesburg' },
  { code: 'RU', name: 'Russia', timezone: 'Europe/Moscow' },
  { code: 'MX', name: 'Mexico', timezone: 'America/Mexico_City' },
  { code: 'AR', name: 'Argentina', timezone: 'America/Argentina/Buenos_Aires' },
  { code: 'SG', name: 'Singapore', timezone: 'Asia/Singapore' },
  { code: 'UTC', name: 'Global (GMT)', timezone: 'UTC' },
]

// Selected country code
const selectedCountry = ref(timezoneStore.countryCode || 'UTC')

// Watch for changes and update the store
watch(selectedCountry, (newValue) => {
  const selected = countryOptions.find((option) => option.code === newValue)
  if (selected) {
    timezoneStore.setCountry(selected.code, selected.timezone)
  }
})

// Initialize on component mount
onMounted(() => {
  // Check if country is stored in localStorage first
  const storedCountry = localStorage.getItem('country_code')
  const storedTimezone = localStorage.getItem('timezone')

  if (storedCountry && storedTimezone) {
    // Use stored country/timezone
    selectedCountry.value = storedCountry
    timezoneStore.setCountry(storedCountry, storedTimezone)
    console.log(`Using stored country: ${storedCountry} with timezone: ${storedTimezone}`)
  } else {
    // No stored preference, detect based on browser
    detectCountry()
  }
})

// Function to detect country based on browser timezone
const detectCountry = () => {
  try {
    // Get browser timezone
    const browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone

    // Find matching country or default to UTC
    const matchingCountry = countryOptions.find((country) => country.timezone === browserTimezone)

    if (matchingCountry) {
      selectedCountry.value = matchingCountry.code
      timezoneStore.setCountry(matchingCountry.code, matchingCountry.timezone)
    } else {
      // Try to find a country in the same timezone region
      const timezoneParts = browserTimezone.split('/')
      if (timezoneParts.length > 1) {
        const timezoneRegion = timezoneParts[0]
        const closeMatch = countryOptions.find((country) =>
          country.timezone.startsWith(timezoneRegion + '/'),
        )

        if (closeMatch) {
          selectedCountry.value = closeMatch.code
          timezoneStore.setCountry(closeMatch.code, closeMatch.timezone)
          return
        }
      }

      // Default to UTC if no match
      selectedCountry.value = 'UTC'
      timezoneStore.setCountry('UTC', 'UTC')
    }
  } catch (error) {
    console.error('Error detecting country/timezone:', error)
    // Default to UTC
    selectedCountry.value = 'UTC'
    timezoneStore.setCountry('UTC', 'UTC')
  }
}

// Get country flag emoji
const getCountryFlagEmoji = (countryCode: string): string => {
  if (countryCode === 'UTC') {
    return '🌐' // Globe for UTC/Global
  }

  // Convert country code to regional indicator symbols (flag emoji)
  return countryCode
    .toUpperCase()
    .split('')
    .map((char) => String.fromCodePoint(char.charCodeAt(0) + 127397))
    .join('')
}

// Get current country name
const currentCountryName = computed(() => {
  const country = countryOptions.find((option) => option.code === selectedCountry.value)
  return country ? country.name : 'Global (GMT)'
})
</script>

<template>
  <div class="country-selector">
    <Dropdown
      v-model="selectedCountry"
      :options="countryOptions"
      optionLabel="name"
      optionValue="code"
      class="country-dropdown-component"
    >
      <template #value="slotProps">
        <div class="flex align-items-center">
          <span class="country-flag">{{ getCountryFlagEmoji(slotProps.value) }}</span>
          <span class="country-name">{{ currentCountryName }}</span>
        </div>
      </template>
      <template #option="slotProps">
        <div class="country-option-item">
          <span class="country-flag">{{ getCountryFlagEmoji(slotProps.option.code) }}</span>
          <span class="country-name">{{ slotProps.option.name }}</span>
        </div>
      </template>
    </Dropdown>
  </div>
</template>

<style lang="scss" scoped>
.flex {
  display: flex;
  align-items: center;
}

.country-flag {
  font-size: 16px;
  margin-right: 8px;
}
</style>
