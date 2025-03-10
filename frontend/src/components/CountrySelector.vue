<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useTimezoneStore } from '@/stores/timezone'

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

// Toggle dropdown visibility
const isDropdownOpen = ref(false)
const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
}

// Close dropdown when clicking outside
const dropdownRef = ref<HTMLElement | null>(null)
const handleClickOutside = (event: MouseEvent) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target as Node)) {
    isDropdownOpen.value = false
  }
}

// Setup and cleanup click handler
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

const onUnmounted = () => {
  document.removeEventListener('click', handleClickOutside)
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
  <div class="country-selector" ref="dropdownRef">
    <button @click="toggleDropdown" class="country-selector-button">
      <span class="country-flag">{{ getCountryFlagEmoji(selectedCountry) }}</span>
      <span class="country-name">{{ currentCountryName }}</span>
      <span class="dropdown-arrow" :class="{ open: isDropdownOpen }">▼</span>
    </button>

    <div v-if="isDropdownOpen" class="country-dropdown">
      <div
        v-for="country in countryOptions"
        :key="country.code"
        class="country-option"
        :class="{ selected: country.code === selectedCountry }"
        @click="
          () => {
            selectedCountry = country.code
            isDropdownOpen = false
          }
        "
      >
        <span class="country-flag">{{ getCountryFlagEmoji(country.code) }}</span>
        <span class="country-name">{{ country.name }}</span>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.country-selector {
  position: relative;
  display: inline-block;
}

.country-selector-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  color: #495057;
  transition: all 0.2s;

  &:hover {
    background: #e9ecef;
  }
}

.country-flag {
  font-size: 16px;
}

.dropdown-arrow {
  font-size: 10px;
  transition: transform 0.2s;

  &.open {
    transform: rotate(180deg);
  }
}

.country-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  width: 220px;
  max-height: 300px;
  overflow-y: auto;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  margin-top: 4px;
}

.country-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.2s;

  &:hover {
    background-color: #f8f9fa;
  }

  &.selected {
    background-color: #e7f5ff;
    font-weight: 500;
  }
}

.country-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 768px) {
  .country-name {
    display: none;
  }

  .country-dropdown {
    width: 180px;

    .country-name {
      display: inline;
    }
  }
}
</style>
