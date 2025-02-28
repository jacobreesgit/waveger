/**
 * A simple 5-line TypeScript utility to toggle password visibility
 *
 * To use directly in HTML:
 * <input type="password" id="passwordField">
 * <button onclick="togglePasswordVisibility('passwordField')">Show/Hide</button>
 */
function togglePasswordVisibility(inputId: string): boolean {
  const input = document.getElementById(inputId) as HTMLInputElement
  const type = input.type === 'password' ? 'text' : 'password'
  input.type = type
  return type === 'text' // Returns true if password is now visible
}

export default togglePasswordVisibility
