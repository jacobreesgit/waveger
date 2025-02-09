import { useChartsStore } from '../stores/charts'

export function useChartHelper() {
  const chartStore = useChartsStore()

  async function loadChartData(chart = 'hot-100', week = '') {
    await chartStore.fetchChartData(chart, week)
  }

  async function loadMoreResults() {
    await chartStore.fetchMoreResults()
  }

  return {
    chartStore,
    loadChartData,
    loadMoreResults,
  }
}
