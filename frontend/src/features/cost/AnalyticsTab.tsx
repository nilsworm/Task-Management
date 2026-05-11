import { useState } from "react"
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"
import { useCostAnalytics, useCostTags } from "@/api/hooks/cost"
import { TagFilterBar } from "./TagFilterBar"

const TOOLTIP_STYLE = {
  background: "var(--color-surface-1)",
  border: "1px solid var(--color-border)",
  borderRadius: 5,
  fontSize: 11,
  color: "var(--color-foreground)",
  boxShadow: "var(--shadow-med)",
}

const TICK_STYLE = {
  fontSize: 9,
  fill: "var(--color-muted-foreground)",
  fontFamily: "var(--font-mono)",
}

const PIE_COLORS = [
  "#00d4ff",
  "#06d6a0",
  "#ffd166",
  "#ff4d6d",
  "#c77dff",
  "#f4a261",
  "#4cc9f0",
  "#7bf1a8",
]

const MONTH_NAMES = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]

function SkeletonBlock({ h }: { h: string }) {
  return <div className={`animate-pulse rounded bg-surface-3 ${h}`} />
}

interface Props {
  year: number
  month: number
}

export function AnalyticsTab({ year, month }: Props) {
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const { data: availableTags = [] } = useCostTags()
  const { data: analytics, isLoading } = useCostAnalytics(
    year,
    month,
    selectedTags.length > 0 ? selectedTags : undefined,
  )

  const pieData = (analytics?.expenses_by_tag ?? []).map((tb, i) => ({
    name: tb.tag,
    value: Number(tb.amount),
    color: PIE_COLORS[i % PIE_COLORS.length],
  }))

  const barData = (analytics?.monthly_comparison ?? []).map((mc) => ({
    name: `${MONTH_NAMES[mc.month - 1]} ${String(mc.year).slice(2)}`,
    Einnahmen: Number(mc.income),
    Ausgaben: Number(mc.expenses),
  }))

  return (
    <div className="flex flex-col gap-6">
      <TagFilterBar
        availableTags={availableTags}
        selectedTags={selectedTags}
        onChange={setSelectedTags}
      />

      {/* Pie Chart */}
      <div className="rounded-[6px] border border-border bg-surface-2 p-4">
        <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.6px] text-muted-foreground">
          Ausgaben nach Tag — {MONTH_NAMES[month - 1]} {year}
        </p>
        {isLoading ? (
          <SkeletonBlock h="h-48" />
        ) : pieData.length === 0 ? (
          <p className="py-12 text-center text-xs text-muted-foreground">
            Keine kategorisierten Ausgaben in diesem Monat.
          </p>
        ) : (
          <div className="flex items-center gap-6">
            <ResponsiveContainer width="50%" height={200}>
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  innerRadius={40}
                  paddingAngle={2}
                >
                  {pieData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={TOOLTIP_STYLE}
                  formatter={(v) => [`${Number(v).toFixed(2)} €`, ""]}
                />
              </PieChart>
            </ResponsiveContainer>
            <ul className="flex flex-col gap-1.5">
              {pieData.map((entry, i) => (
                <li key={i} className="flex items-center gap-2 text-[11px]">
                  <span
                    className="h-2.5 w-2.5 shrink-0 rounded-sm"
                    style={{ background: entry.color }}
                  />
                  <span className="text-muted-foreground">{entry.name}</span>
                  <span className="font-mono font-semibold">{entry.value.toFixed(2)} €</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Bar Chart */}
      <div className="rounded-[6px] border border-border bg-surface-2 p-4">
        <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.6px] text-muted-foreground">
          Einnahmen vs. Ausgaben — letzte 6 Monate
        </p>
        {isLoading ? (
          <SkeletonBlock h="h-48" />
        ) : barData.every((d) => d.Einnahmen === 0 && d.Ausgaben === 0) ? (
          <p className="py-12 text-center text-xs text-muted-foreground">
            Keine Daten für die letzten 6 Monate.
          </p>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={barData} barGap={2} barCategoryGap="30%">
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--color-border)"
                vertical={false}
              />
              <XAxis dataKey="name" tick={TICK_STYLE} axisLine={false} tickLine={false} />
              <YAxis
                tick={TICK_STYLE}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v) => `${v}€`}
              />
              <Tooltip
                contentStyle={TOOLTIP_STYLE}
                formatter={(v) => [`${Number(v).toFixed(2)} €`, ""]}
              />
              <Legend
                wrapperStyle={{ fontSize: 11, color: "var(--color-muted-foreground)" }}
              />
              <Bar dataKey="Einnahmen" fill="#06d6a0" radius={[3, 3, 0, 0]} />
              <Bar dataKey="Ausgaben" fill="#ff4d6d" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
