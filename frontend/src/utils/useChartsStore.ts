import { useChartsStore } from '@/stores/charts'

export function useCharts() {
  const store = useChartsStore()

  const loadDefaultChart = async () => {
    await store.fetchChartDetails() // Defaults to "hot-100"
    console.log('Default Chart with Apple Music Data:', store.chartDetails)
  }

  return {
    store,
    loadDefaultChart,
  }
}
