import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts"
import type { MetricsData } from "@/api/hooks/dashboard"

const STATUS_COLORS: Record<string, string> = {
  backlog:     "#5a5a7a",
  todo:        "#9090b0",
  in_progress: "#00d4ff",
  review:      "#ffd166",
  blocked:     "#ff4d6d",
  done:        "#06d6a0",
  cancelled:   "#333350",
}

const STATUS_LABELS: Record<string, string> = {
  backlog:     "Backlog",
  todo:        "To Do",
  in_progress: "In Progress",
  review:      "Review",
  blocked:     "Blocked",
  done:        "Done",
  cancelled:   "Cancelled",
}

const TOOLTIP_STYLE = {
  background: "var(--color-surface-1)",
  border: "1px solid var(--color-border)",
  borderRadius: 5,
  fontSize: 11,
  color: "var(--color-foreground)",
  boxShadow: "var(--shadow-med)",
}

interface Props { metrics: MetricsData }

export function MetricsWidget({ metrics }: Props) {
  const { task_counts, completion_rate } = metrics
  const total = Object.values(task_counts).reduce((s, n) => s + n, 0)

  const pieData = Object.entries(task_counts)
    .filter(([, v]) => v > 0)
    .map(([key, value]) => ({
      name: STATUS_LABELS[key] ?? key,
      value,
      color: STATUS_COLORS[key] ?? "#5a5a7a",
    }))

  return (
    <div className="flex flex-col gap-3.5 rounded-[6px] border border-border bg-surface-2 p-3.5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold uppercase tracking-[0.6px] text-muted-foreground">
          Task Metrics
        </span>
        <span
          className="rounded bg-surface-3 px-2 py-0.5 font-mono text-[10px] font-semibold"
          style={{ color: "var(--color-cyan)" }}
        >
          {completion_rate.toFixed(0)}% complete
        </span>
      </div>

      {total === 0 ? (
        <p className="py-8 text-center text-[11px] text-muted-foreground">No tasks yet.</p>
      ) : (
        <>
          {/* Donut chart + legend */}
          <div className="flex items-center gap-4">
            <ResponsiveContainer width={140} height={110}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={32}
                  outerRadius={52}
                  dataKey="value"
                  strokeWidth={0}
                >
                  {pieData.map((entry, i) => (
                    <Cell
                      key={i}
                      fill={entry.color}
                      style={{ filter: `drop-shadow(0 0 4px ${entry.color}60)` }}
                    />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={TOOLTIP_STYLE}
                  itemStyle={{ color: "var(--color-foreground)" }}
                />
              </PieChart>
            </ResponsiveContainer>

            {/* Inline legend */}
            <div className="flex flex-col gap-1.5">
              {pieData.map((s) => (
                <div key={s.name} className="flex items-center gap-1.5">
                  <span
                    className="h-2 w-2 shrink-0 rounded-[2px]"
                    style={{ background: s.color }}
                  />
                  <span className="text-[11px] text-muted-foreground">{s.name}</span>
                  <span
                    className="ml-auto pl-2 font-mono text-[11px] font-semibold"
                    style={{ color: s.color }}
                  >
                    {Math.round((s.value / total) * 100)}%
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Count table */}
          <div className="border-t border-border pt-2">
            <table className="w-full">
              <tbody>
                {Object.entries(task_counts).map(([key, count]) => (
                  <tr key={key}>
                    <td className="py-0.5 text-[11px] text-muted-foreground">
                      {STATUS_LABELS[key]}
                    </td>
                    <td
                      className="py-0.5 text-right font-mono text-[11px] font-semibold tabular-nums"
                      style={{ color: STATUS_COLORS[key] }}
                    >
                      {count}
                    </td>
                  </tr>
                ))}
                <tr className="border-t border-border">
                  <td className="pt-1 text-[11px] font-semibold text-foreground">Total</td>
                  <td className="pt-1 text-right font-mono text-[11px] font-bold text-foreground tabular-nums">
                    {total}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
