"use client"

import { ChevronDown, ChevronUp } from "lucide-react"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"

export type MetricItem = {
  label: string
  value: React.ReactNode
  trend?: "up" | "down"
}

type AnalyticsFooterProps = {
  title: string
  items: MetricItem[]
  columns?: 2 | 3
}

export function AnalyticsFooter({
  title,
  items,
  columns = 3,
}: AnalyticsFooterProps) {
  return (
    <footer className="flex flex-col gap-5 border-t border-border bg-muted/30 px-6 py-6">
      <h3 className="font-zodiak text-base font-semibold tracking-tight text-foreground">
        {title}
      </h3>
      <Separator className="w-full" />
      <div
        className={cn(
          "grid gap-4",
          columns === 2 ? "grid-cols-1 sm:grid-cols-2" : "grid-cols-1 sm:grid-cols-3"
        )}
      >
        {items.map((item, i) => (
          <div
            key={i}
            className="flex min-h-0 flex-col gap-2 rounded-lg border border-border bg-background px-5 py-4"
          >
            <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              {item.label}
            </div>
            <div className="flex min-h-7 items-baseline justify-between gap-2">
              {item.trend != null ? (
                <span
                  className={cn(
                    "inline-flex items-center gap-1 font-mono text-base font-semibold tabular-nums",
                    item.trend === "up"
                      ? "text-emerald-600 dark:text-emerald-400"
                      : "text-red-600 dark:text-red-400"
                  )}
                >
                  {item.value}
                  {item.trend === "up" ? (
                    <ChevronUp className="size-4 shrink-0" aria-hidden />
                  ) : (
                    <ChevronDown className="size-4 shrink-0" aria-hidden />
                  )}
                </span>
              ) : (
                <span className="font-mono text-base font-semibold tabular-nums text-foreground">
                  {item.value}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </footer>
  )
}
