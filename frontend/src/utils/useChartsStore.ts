import { useChartsStore } from '@/stores/charts'

export function useCharts() {
  const chartsStore = useChartsStore()

  const loadAppleMusicToken = async () => {
    await chartsStore.fetchAppleMusicToken()
    console.log('Apple Music Token: ' + chartsStore.appleMusicToken)
  }

  const loadChartTypes = async () => {
    await chartsStore.fetchTopCharts()
    console.log(chartsStore.topCharts)
  }

  const loadDefaultChart = async ({
    chartId = 'hot-100',
    week = new Date().toISOString().split('T')[0], // Default to today's date
    range = '1-3',
  } = {}) => {
    try {
      await chartsStore.fetchChartDetails(chartId, week, range)
      console.log(chartsStore.chartDetails)
    } catch (error) {
      console.error('Error loading chart details:', error)
    }
  }

  return {
    chartsStore,
    loadAppleMusicToken,
    loadDefaultChart,
    loadChartTypes,
  }
}
