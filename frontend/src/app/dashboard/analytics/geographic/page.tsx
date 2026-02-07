"use client"

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { AnalyticsFooter } from "../analytics-footer"
import { geographicHotSpotsData, geographicSummary } from "../data"
import { cn } from "@/lib/utils"

function heatColor(value: number, min: number, max: number): string {
  if (max === min) return "oklch(0.75 0.12 145)"
  const t = (value - min) / (max - min)
  if (t < 0.5) {
    const s = t * 2
    return `oklch(${0.75 - s * 0.2} 0.15 ${145 - s * 50})`
  }
  const s = (t - 0.5) * 2
  return `oklch(${0.65 - s * 0.15} 0.2 ${50 - s * 50})`
}

export default function GeographicPage() {
  const slowP90Values = geographicHotSpotsData.map((d) => d.slow_p90)
  const minP90 = Math.min(...slowP90Values)
  const maxP90 = Math.max(...slowP90Values)

  return (
    <div className="min-h-0 w-full min-w-0 flex-1 space-y-6 overflow-auto py-2">
      <Card>
        <CardHeader>
          <CardTitle>Geographic hot spots</CardTitle>
          <CardDescription>
            Electoral districts by volume, unresolved count, and slow_p90 (days). Color = slow_p90 intensity (green = faster, red = slower).
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto rounded-lg border bg-card">
            <table className="w-full min-w-[320px] border-collapse text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-3 py-2.5 text-left font-medium">District</th>
                  <th className="px-3 py-2.5 text-right font-medium">Volume</th>
                  <th className="px-3 py-2.5 text-right font-medium">Unresolved</th>
                  <th className="px-3 py-2.5 text-right font-medium">Slow (p90)</th>
                </tr>
              </thead>
              <tbody>
                {geographicHotSpotsData.map((row) => (
                  <tr
                    key={row.district}
                    className="border-b border-border/50 transition-colors hover:bg-muted/30"
                  >
                    <td className="px-3 py-2 font-medium">{row.district}</td>
                    <td className="px-3 py-2 text-right tabular-nums">{row.volume.toLocaleString()}</td>
                    <td className="px-3 py-2 text-right tabular-nums">{row.unresolved}</td>
                    <td
                      className={cn(
                        "px-3 py-2 text-right tabular-nums font-medium text-foreground"
                      )}
                      style={{
                        backgroundColor: heatColor(row.slow_p90, minP90, maxP90),
                      }}
                    >
                      {typeof row.slow_p90 === "number"
                        ? row.slow_p90.toFixed(1)
                        : row.slow_p90}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            Color intensity: green = lower slow_p90, red = higher (hotter).
          </p>
        </CardContent>
        <CardFooter className="p-0">
          <AnalyticsFooter
            title="Key metrics"
            columns={3}
            items={[
              { label: "Districts", value: geographicSummary.totalDistricts },
              {
                label: "Highest volume",
                value: `${geographicSummary.highestVolume.district} (${geographicSummary.highestVolume.volume.toLocaleString()})`,
              },
              {
                label: "Slowest p90",
                value: `${geographicSummary.slowestP90.district} (${geographicSummary.slowestP90.slow_p90} days)`,
              },
            ]}
          />
        </CardFooter>
      </Card>
    </div>
  )
}
