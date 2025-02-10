import { useChartsStore } from '@/stores/charts'

export function useCharts() {
  const chartsStore = useChartsStore()

  const loadDefaultChart = async () => {
    await chartsStore.fetchChartDetails() // Defaults to "hot-100"
    console.log(
      'Default Chart with Apple Music Data:',
      chartsStore.chartDetails
    )
  }

  return {
    chartsStore,
    loadDefaultChart,
  }
}
