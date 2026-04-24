import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts"
import type { MetricsData } from "@/api/hooks/dashboard"

const STATUS_COLORS: Record<string, string> = {
  backlog: "#94a3b8",
  todo: "#60a5fa",
  in_progress: "#f59e0b",
  review: "#a78bfa",
  blocked: "#f87171",
  done: "#34d399",
  cancelled: "#6b7280",
}

const STATUS_LABELS: Record<string, string> = {
  backlog: "Backlog",
  todo: "To Do",
  in_progress: "In Progress",
  review: "Review",
  blocked: "Blocked",
  done: "Done",
  cancelled: "Cancelled",
}

interface Props {
  metrics: MetricsData
}

export function MetricsWidget({ metrics }: Props) {
  const { task_counts, completion_rate } = metrics

  const pieData = Object.entries(task_counts)
    .filter(([, v]) => v > 0)
    .map(([key, value]) => ({
      name: STATUS_LABELS[key] ?? key,
      value,
      color: STATUS_COLORS[key] ?? "#94a3b8",
    }))

  const total = Object.values(task_counts).reduce((s, n) => s + n, 0)

  return (
    <div className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold">Task Metrics</h2>
        <span className="text-xs text-muted-foreground">
          {completion_rate.toFixed(0)}% complete
        </span>
      </div>

      {total === 0 ? (
        <p className="py-4 text-center text-xs text-muted-foreground">No tasks yet.</p>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={65}
                dataKey="value"
                strokeWidth={0}
              >
                {pieData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value, name) => [value, name]}
                contentStyle={{ fontSize: 12 }}
              />
              <Legend iconSize={8} iconType="circle" wrapperStyle={{ fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>

          <table className="w-full text-xs">
            <tbody>
              {Object.entries(task_counts).map(([key, count]) => (
                <tr key={key}>
                  <td className="py-0.5 text-muted-foreground">{STATUS_LABELS[key]}</td>
                  <td className="py-0.5 text-right tabular-nums">{count}</td>
                </tr>
              ))}
              <tr className="border-t border-border font-medium">
                <td className="pt-1">Total</td>
                <td className="pt-1 text-right tabular-nums">{total}</td>
              </tr>
            </tbody>
          </table>
        </>
      )}
    </div>
  )
}
