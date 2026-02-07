"use client"

import {
  CartesianGrid,
  Scatter,
  ScatterChart,
  Text,
  XAxis,
  YAxis,
  ZAxis,
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
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"
import { AnalyticsFooter } from "../analytics-footer"
import { priorityQuadrantData, prioritySummary } from "../data"

const config: ChartConfig = {
  time_to_close_days: { label: "Time to close (days)" },
  request_count: { label: "Request count" },
  group: { label: "Category" },
  priority_category: { label: "Priority" },
}

export default function PriorityQuadrantPage() {
  return (
    <div className="min-h-0 w-full min-w-0 flex-1 space-y-6 overflow-auto py-2">
      <Card>
        <CardHeader>
          <CardTitle>Priority quadrant</CardTitle>
          <CardDescription>
            Categories by time to close (x) and request count (y). Bubble size = open count. Focus on high time + high volume.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ChartContainer config={config} className="h-[320px] w-full">
            <ScatterChart margin={{ left: 48, right: 12, bottom: 28, top: 8 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis
                type="number"
                dataKey="time_to_close_days"
                tickLine={false}
                axisLine={false}
                label={{ value: "Time to close (days)", position: "insideBottom", offset: -8 }}
              />
              <YAxis
                type="number"
                dataKey="request_count"
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) => v.toLocaleString()}
                label={{
                  value: "Request count",
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
              <ZAxis type="number" dataKey="bubble_size" range={[50, 400]} name="Open count" />
              <ChartTooltip content={<ChartTooltipContent />} cursor={{ strokeDasharray: "3 3" }} />
              <Scatter
                data={priorityQuadrantData}
                name="Category"
                fill="var(--chart-1)"
                fillOpacity={0.7}
              />
            </ScatterChart>
          </ChartContainer>
        </CardContent>
        <CardFooter className="p-0">
          <AnalyticsFooter
            title="Summary"
            columns={3}
            items={[
              {
                label: "High priority (systemic)",
                value: `${prioritySummary.highPriorityCount} categories`,
              },
              {
                label: "Total requests",
                value: prioritySummary.totalRequests.toLocaleString(),
              },
              {
                label: "Avg time to close",
                value: `${prioritySummary.avgTimeToClose} days`,
              },
            ]}
          />
        </CardFooter>
      </Card>
    </div>
  )
}
