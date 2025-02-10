import { useChartsStore } from '@/stores/charts'

export function useCharts() {
  const chartsStore = useChartsStore()

  const loadDefaultChart = async () => {
    await chartsStore.fetchChartDetails()
    console.log(chartsStore.chartDetails)
  }

  return {
    chartsStore,
    loadDefaultChart,
  }
}
