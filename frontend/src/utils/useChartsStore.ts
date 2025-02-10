import { useChartsStore } from '@/stores/charts'

export function useCharts() {
  const chartsStore = useChartsStore()

  const loadDefaultChart = async () => {
    const defaultChartId = 'hot-100' // Default chart
    const defaultWeek = new Date().toISOString().split('T')[0] // Today's date in YYYY-MM-DD format
    const defaultRange = '1-9' // Defualt range

    await chartsStore.fetchChartDetails(
      defaultChartId,
      defaultWeek,
      defaultRange
    )
    console.log(chartsStore.chartDetails)
  }

  return {
    chartsStore,
    loadDefaultChart,
  }
}
