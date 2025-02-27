import axios from 'axios'

export interface ValidationResult {
  isValid: boolean
  errors: {
    username?: string
    email?: string
    password?: string
    general?: string
  }
}

export interface LoginValidationResult {
  isValid: boolean
  errors: {
    username?: string
    password?: string
    general?: string
  }
}

/**
 * Validates login form inputs
 * @param username The username to validate
 * @param password The password to validate
 * @returns A validation result object
 */
export function validateLoginForm(username: string, password: string): LoginValidationResult {
  const errors: LoginValidationResult['errors'] = {}

  // Username validation
  if (!username) {
    errors.username = 'Username is required'
  } else if (username.length < 3) {
    errors.username = 'Username must be at least 3 characters long'
  } else if (username.length > 20) {
    errors.username = 'Username cannot exceed 20 characters'
  }

  // Password validation
  if (!password) {
    errors.password = 'Password is required'
  } else if (password.length < 8) {
    errors.password = 'Password must be at least 8 characters long'
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  }
}

export async function validateRegistrationForm(
  username: string,
  email: string,
  password: string,
): Promise<ValidationResult> {
  const errors: ValidationResult['errors'] = {}

  // Username validation
  if (!username) {
    errors.username = 'Username is required'
  } else if (username.length < 3) {
    errors.username = 'Username must be at least 3 characters long'
  } else if (username.length > 20) {
    errors.username = 'Username cannot exceed 20 characters'
  } else if (!/^[a-zA-Z0-9_]+$/.test(username)) {
    errors.username = 'Username can only contain letters, numbers, and underscores'
  }

  // Email validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!email) {
    errors.email = 'Email is required'
  } else if (!emailRegex.test(email)) {
    errors.email = 'Please enter a valid email address'
  }

  // Password validation
  if (!password) {
    errors.password = 'Password is required'
  } else if (password.length < 8) {
    errors.password = 'Password must be at least 8 characters long'
  } else {
    // Password strength checks
    const hasUppercase = /[A-Z]/.test(password)
    const hasLowercase = /[a-z]/.test(password)
    const hasNumber = /[0-9]/.test(password)
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password)

    if (!(hasUppercase && hasLowercase && hasNumber && hasSpecialChar)) {
      errors.password = 'Password must include uppercase, lowercase, number, and special character'
    }
  }

  // If there are basic validation errors, return early
  if (Object.keys(errors).length > 0) {
    return {
      isValid: false,
      errors,
    }
  }

  // Check username and email availability
  try {
    const BASE_URL = 'https://wavegerpython.onrender.com/api/auth'

    // Check username availability
    const usernameResponse = await axios.get(`${BASE_URL}/check-availability`, {
      params: { username },
    })
    if (usernameResponse.data.username_exists) {
      errors.username = 'Username is already taken'
    }

    // Check email availability
    const emailResponse = await axios.get(`${BASE_URL}/check-availability`, {
      params: { email },
    })
    if (emailResponse.data.email_exists) {
      errors.email = 'Email is already registered'
    }

    return {
      isValid: Object.keys(errors).length === 0,
      errors,
    }
  } catch (error) {
    // If availability check fails, consider it a validation error
    return {
      isValid: false,
      errors: {
        ...errors,
        general: 'Unable to complete registration check. Please try again.',
      },
    }
  }
}

// Availability checking functions
export async function checkUsernameAvailability(username: string): Promise<boolean> {
  try {
    const BASE_URL = 'https://wavegerpython.onrender.com/api/auth'
    const response = await axios.get(`${BASE_URL}/check-availability`, {
      params: { username },
    })
    return !response.data.username_exists
  } catch (error) {
    console.error('Username availability check failed:', error)
    throw error
  }
}

export async function checkEmailAvailability(email: string): Promise<boolean> {
  try {
    const BASE_URL = 'https://wavegerpython.onrender.com/api/auth'
    const response = await axios.get(`${BASE_URL}/check-availability`, {
      params: { email },
    })
    return !response.data.email_exists
  } catch (error) {
    console.error('Email availability check failed:', error)
    throw error
  }
}

// Add these functions to frontend/src/utils/validation.ts

export interface PasswordValidationResult {
  isValid: boolean
  errors: string[]
}

/**
 * Validates a password for strength and security
 * @param password The password to validate
 * @returns Validation result with errors if invalid
 */
export function validatePassword(password: string): PasswordValidationResult {
  const errors: string[] = []

  if (!password) {
    errors.push('Password is required')
    return { isValid: false, errors }
  }

  if (password.length < 8) {
    errors.push('Password must be at least 8 characters long')
  }

  // Check for password strength
  const hasUppercase = /[A-Z]/.test(password)
  const hasLowercase = /[a-z]/.test(password)
  const hasNumber = /[0-9]/.test(password)
  const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password)

  if (!(hasUppercase && hasLowercase && hasNumber && hasSpecialChar)) {
    errors.push('Password must include uppercase, lowercase, number, and special character')
  }

  return {
    isValid: errors.length === 0,
    errors,
  }
}

/**
 * Validates email format
 * @param email Email to validate
 * @returns True if email format is valid
 */
export function validateEmail(email: string): boolean {
  if (!email) return false

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * Validates that passwords match for password confirmation
 * @param password The password
 * @param confirmPassword The confirmation password
 * @returns True if passwords match
 */
export function passwordsMatch(password: string, confirmPassword: string): boolean {
  return password === confirmPassword
}
