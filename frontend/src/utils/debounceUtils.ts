import _ from 'lodash'

/**
 * Creates a debounced function that delays invoking func until after wait milliseconds
 * have elapsed since the last time the debounced function was invoked.
 *
 * @param func The function to debounce
 * @param wait The number of milliseconds to delay
 * @param options The lodash debounce options
 * @returns A debounced function
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait = 300,
  options: _.DebounceSettings = {},
): _.DebouncedFunc<T> => {
  return _.debounce(func, wait, options)
}

/**
 * Creates a throttled function that only invokes func at most once per every wait milliseconds.
 *
 * @param func The function to throttle
 * @param wait The number of milliseconds to throttle invocations to
 * @param options The lodash throttle options
 * @returns A throttled function
 */
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  wait = 300,
  options: _.ThrottleSettings = {},
): _.DebouncedFunc<T> => {
  return _.throttle(func, wait, options)
}

/**
 * Debounces an event handler for Vue input events
 *
 * @param handler The function to call after debouncing
 * @param wait The number of milliseconds to delay
 * @returns A debounced function that extracts the value from the event
 */
export const debounceInputHandler = <T>(
  handler: (value: string) => void,
  wait = 300,
): ((event: Event) => void) => {
  const debouncedFn = _.debounce(handler, wait)

  return (event: Event) => {
    const target = event.target as HTMLInputElement
    debouncedFn(target.value)
  }
}

/**
 * Creates a debounced async function that updates a loading state
 *
 * @param func The async function to debounce
 * @param loadingRef The ref to update with loading state
 * @param wait The number of milliseconds to delay
 * @returns A debounced function that handles loading state
 */
export const debounceWithLoading = <T extends (...args: any[]) => Promise<any>>(
  func: T,
  loadingRef: { value: boolean },
  wait = 300,
): ((...funcArgs: Parameters<T>) => Promise<void>) => {
  const debouncedFn = _.debounce(async (...args: Parameters<T>) => {
    try {
      loadingRef.value = true
      await func(...args)
    } finally {
      loadingRef.value = false
    }
  }, wait)

  return async (...args: Parameters<T>) => {
    loadingRef.value = true
    debouncedFn(...args)
  }
}
