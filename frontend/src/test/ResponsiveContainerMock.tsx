import { cloneElement, type ReactElement } from 'react'

type ChartChild = ReactElement<{ height?: number; width?: number }>

export function TestResponsiveContainer({ children }: { children: ChartChild }) {
  return <div style={{ height: 320, width: 800 }}>{cloneElement(children, { height: 320, width: 800 })}</div>
}
