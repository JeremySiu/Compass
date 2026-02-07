"use client"

import {
  CartesianGrid,
  Line,
  LineChart,
  Text,
  XAxis,
  YAxis,
} from "recharts"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"
import { AnalyticsFooter } from "../analytics-footer"
import { frequencyLineData, frequencyLatestChange } from "../data"

const config: ChartConfig = {
  time: { label: "Time" },
  garbage: { label: "Garbage, recycling and organics", color: "var(--chart-1)" },
  roads: { label: "Roads, traffic and sidewalks", color: "var(--chart-2)" },
  recreation: { label: "Recreation and leisure", color: "var(--chart-3)" },
}

export default function FrequencyPage() {
  return (
    <div className="min-h-0 w-full min-w-0 flex-1 space-y-6 overflow-auto py-2">
      <Card>
        <CardHeader>
          <CardTitle>Frequency over time</CardTitle>
          <CardDescription>
            Request volume by category across time periods. Compare trends for Garbage, Roads, and Recreation.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ChartContainer config={config} className="h-[320px] w-full">
            <LineChart data={frequencyLineData} margin={{ left: 40, right: 12, bottom: 24, top: 8 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="time"
                tickLine={false}
                axisLine={false}
                label={{ value: "Time", position: "insideBottom", offset: -8 }}
              />
              <YAxis
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) => v.toLocaleString()}
                label={{
                  value: "Request volume",
                  content: (props: {
                    viewBox?: { x: number; y: number; width: number; height: number }
                    value?: string
                  }) => {
                    const vb = props.viewBox
                    if (!vb) return null
                    const x = vb.x - 20
                    const y = vb.y + vb.height / 2
                    return (
                      <Text x={x} y={y} textAnchor="middle" verticalAnchor="middle" angle={-90}>
                        {props.value}
                      </Text>
                    )
                  },
                }}
              />
              <ChartTooltip content={<ChartTooltipContent indicator="line" />} />
              <ChartLegend align="right" verticalAlign="top" content={<ChartLegendContent />} />
              <Line type="linear" dataKey="garbage" stroke="var(--color-garbage)" strokeWidth={2} dot={false} />
              <Line type="linear" dataKey="roads" stroke="var(--color-roads)" strokeWidth={2} dot={false} />
              <Line type="linear" dataKey="recreation" stroke="var(--color-recreation)" strokeWidth={2} dot={false} />
            </LineChart>
          </ChartContainer>
        </CardContent>
        <CardFooter className="p-0">
          <AnalyticsFooter
            title={`Latest change: ${frequencyLatestChange.period}`}
            columns={3}
            items={frequencyLatestChange.series.map((s) => ({
              label: s.label.split(",")[0],
              value: `${s.changePct >= 0 ? "+" : ""}${s.changePct}%`,
              trend: s.changePct >= 0 ? "up" : "down",
            }))}
          />
        </CardFooter>
      </Card>
    </div>
  )
}
