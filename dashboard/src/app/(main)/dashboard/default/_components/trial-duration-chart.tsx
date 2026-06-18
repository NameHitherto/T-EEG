"use client";

import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";

import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import type { SeedVSessionTrials } from "@/types/seed-v";

const SESSION_COLORS: Record<string, string> = {
  "1": "var(--chart-1)",
  "2": "var(--chart-2)",
  "3": "var(--chart-3)",
};

const chartConfig = {
  duration_s: { label: "Duration (s)" },
} satisfies ChartConfig;

export function TrialDurationChart({ trials }: { readonly trials: SeedVSessionTrials }) {
  const data = Object.entries(trials).flatMap(([session, list]) =>
    list.map((t) => ({
      session,
      trial: `S${session}·${t.trial}`,
      duration_s: t.duration_s,
      fill: SESSION_COLORS[session] ?? "var(--chart-1)",
    })),
  );

  return (
    <ChartContainer config={chartConfig} className="h-[220px] w-full">
      <BarChart data={data} margin={{ left: 4, right: 4, top: 8, bottom: 0 }}>
        <CartesianGrid vertical={false} className="stroke-border" />
        <XAxis
          dataKey="trial"
          tickLine={false}
          axisLine={false}
          tickMargin={6}
          interval="preserveStartEnd"
          tick={{ fontSize: 9 }}
        />
        <YAxis tickLine={false} axisLine={false} width={28} tick={{ fontSize: 10 }} unit="s" />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Bar dataKey="duration_s" radius={3} />
      </BarChart>
    </ChartContainer>
  );
}
