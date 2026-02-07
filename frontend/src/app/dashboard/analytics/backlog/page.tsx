"use client"

import {
  Bar,
  BarChart,
  CartesianGrid,
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
import { backlogBarData, backlogSummary } from "../data"

const config: ChartConfig = {
  category: { label: "Category" },
  total_unresolved: { label: "Total unresolved", color: "var(--chart-1)" },
}

export default function BacklogPage() {
  return (
    <div className="min-h-0 w-full min-w-0 flex-1 space-y-6 overflow-auto py-2">
      <Card>
        <CardHeader>
          <CardTitle>Backlog rank list</CardTitle>
          <CardDescription>
            Service Level 1 categories by total unresolved requests. Longest-standing open items.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ChartContainer config={config} className="h-[320px] w-full">
            <BarChart data={backlogBarData} layout="vertical" margin={{ left: 36, right: 12, bottom: 28, top: 8 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis
                type="number"
                tickLine={false}
                axisLine={false}
                label={{ value: "Total unresolved", position: "insideBottom", offset: -8 }}
              />
              <YAxis
                type="category"
                dataKey="category"
                width={180}
                tick={{ fontSize: 11 }}
                tickLine={false}
                axisLine={false}
                label={{
                  value: "Category",
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
              <ChartLegend content={<ChartLegendContent />} />
              <Bar dataKey="total_unresolved" fill="var(--color-total_unresolved)" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ChartContainer>
        </CardContent>
        <CardFooter className="p-0">
          <AnalyticsFooter
            title="Latest snapshot"
            columns={2}
            items={[
              { label: "Total unresolved", value: backlogSummary.totalUnresolved },
              {
                label: "Highest",
                value: `${backlogSummary.topCategory.split(",")[0]} (${backlogSummary.topValue})`,
              },
            ]}
          />
        </CardFooter>
      </Card>
    </div>
  )
}
