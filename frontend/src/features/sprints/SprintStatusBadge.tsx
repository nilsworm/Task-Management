const LABELS: Record<string, string> = {
  planned:   "Planned",
  active:    "Active",
  completed: "Completed",
  cancelled: "Cancelled",
}

const COLORS: Record<string, string> = {
  planned:   "#9090b0",
  active:    "#00d4ff",
  completed: "#06d6a0",
  cancelled: "#5a5a7a",
}

export function SprintStatusBadge({ status }: { status: string }) {
  const color = COLORS[status] ?? "#9090b0"
  return (
    <span
      className="inline-flex items-center rounded-[3px] px-1.5 py-0.5 font-mono text-[10px] font-semibold"
      style={{ background: `${color}22`, color }}
    >
      {LABELS[status] ?? status}
    </span>
  )
}
