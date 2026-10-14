const integerFormatter = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 })

export function formatInteger(value: number): string {
  return integerFormatter.format(value)
}

export function formatPercentage(value: number | null): string {
  if (value === null) return '—'
  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    maximumFractionDigits: value > 0 && value < 0.01 ? 1 : 0,
  }).format(value)
}

export function formatDateTime(value: string | null): string {
  if (!value) return 'Never observed'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Invalid timestamp'
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    timeZoneName: 'short',
  }).format(date)
}

export function formatChartDate(value: string): string {
  const date = new Date(`${value}T00:00:00Z`)
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  }).format(date)
}
