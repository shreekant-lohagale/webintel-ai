export function errorMessage(error: Error): string {
  return error.message || 'An unexpected error occurred.'
}
