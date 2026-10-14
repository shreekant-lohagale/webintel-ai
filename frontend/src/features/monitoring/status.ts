import type { FreshnessStatus } from '../../types/monitoring'

export const freshnessLabels: Record<FreshnessStatus, string> = {
  recently_observed: 'Recently observed',
  aging_observation: 'Aging observation',
  stale_observation: 'Stale observation',
  future_timestamp: 'Future timestamp',
  unknown: 'Unknown',
}
