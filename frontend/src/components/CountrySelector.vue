<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useTimezoneStore } from '@/stores/timezone'
import Select from 'primevue/select'

const timezoneStore = useTimezoneStore()

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

const selectedCountry = ref(timezoneStore.countryCode || 'UTC')

watch(selectedCountry, (newValue) => {
  const selected = countryOptions.find((option) => option.code === newValue)
  if (selected) {
    timezoneStore.setCountry(selected.code, selected.timezone)
  }
})

onMounted(() => {
  const storedCountry = localStorage.getItem('country_code')
  const storedTimezone = localStorage.getItem('timezone')

  if (storedCountry && storedTimezone) {
    selectedCountry.value = storedCountry
    timezoneStore.setCountry(storedCountry, storedTimezone)
    console.log(`Using stored country: ${storedCountry} with timezone: ${storedTimezone}`)
  } else {
    detectCountry()
  }
})

// Function to detect country based on browser timezone
const detectCountry = () => {
  try {
    const browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone
    const matchingCountry = countryOptions.find((country) => country.timezone === browserTimezone)

    if (matchingCountry) {
      selectedCountry.value = matchingCountry.code
      timezoneStore.setCountry(matchingCountry.code, matchingCountry.timezone)
    } else {
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

const getCountryFlagEmoji = (countryCode: string): string => {
  if (countryCode === 'UTC') {
    return '🌐'
  }
  return countryCode
    .toUpperCase()
    .split('')
    .map((char) => String.fromCodePoint(char.charCodeAt(0) + 127397))
    .join('')
}

const currentCountryName = computed(() => {
  const country = countryOptions.find((option) => option.code === selectedCountry.value)
  return country ? country.name : 'Global (GMT)'
})
</script>

<template>
  <Select
    v-model="selectedCountry"
    :options="countryOptions"
    optionLabel="name"
    optionValue="code"
    class="country-selector"
  >
    <template #value="slotProps">
      <div class="country-selector__value flex items-center">
        <span class="country-selector__value__country-flag text-base">{{
          getCountryFlagEmoji(slotProps.value)
        }}</span>
        <span class="country-selector__value__country-name hidden">{{ currentCountryName }}</span>
      </div>
    </template>
    <template #option="slotProps">
      <div class="country-selector__item flex items-center">
        <span class="country-selector__item__country-flag text-base mr-2">{{
          getCountryFlagEmoji(slotProps.option.code)
        }}</span>
        <span class="country-selector__item__country-name inline">{{ slotProps.option.name }}</span>
      </div>
    </template>
  </Select>
</template>
