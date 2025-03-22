// UI Component Types

/**
 * LoadingSpinner component props
 */
export interface LoadingSpinnerProps {
  /**
   * Size of the spinner
   * @default 'medium'
   */
  size?: 'small' | 'medium' | 'large' | 'custom'

  /**
   * Custom size value (CSS value)
   */
  customSize?: string

  /**
   * Width of the spinner stroke
   * @default '4px'
   */
  strokeWidth?: string

  /**
   * Background fill color
   * @default '#f3f3f3'
   */
  fill?: string

  /**
   * Animation duration
   * @default '1s'
   */
  animationDuration?: string

  /**
   * Loading text to display
   * @default 'Loading...'
   */
  label?: string

  /**
   * Whether to center the spinner in its container
   * @default false
   */
  centerInContainer?: boolean
}
