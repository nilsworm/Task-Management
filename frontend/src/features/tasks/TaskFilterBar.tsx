import { AlertCircle, Search } from "lucide-react"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

const STATUS_OPTIONS = [
  { value: "all",         label: "All statuses" },
  { value: "backlog",     label: "Backlog" },
  { value: "todo",        label: "To Do" },
  { value: "in_progress", label: "In Progress" },
  { value: "review",      label: "Review" },
  { value: "blocked",     label: "Blocked" },
  { value: "done",        label: "Done" },
  { value: "cancelled",   label: "Cancelled" },
]

const PRIORITY_OPTIONS = [
  { value: "all",      label: "All priorities" },
  { value: "low",      label: "Low" },
  { value: "medium",   label: "Medium" },
  { value: "high",     label: "High" },
  { value: "critical", label: "Critical" },
]

const TYPE_OPTIONS = [
  { value: "all",       label: "All types" },
  { value: "daily",     label: "Daily" },
  { value: "sprint",    label: "Sprint" },
  { value: "goal",      label: "Goal" },
  { value: "milestone", label: "Milestone" },
]

export interface TaskFilters {
  search: string
  overdue: boolean
  status: string
  priority: string
  taskType: string
}

interface Props {
  filters: TaskFilters
  onChange: (f: TaskFilters) => void
}

export function TaskFilterBar({ filters, onChange }: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      <div className="relative flex items-center">
        <Search className="pointer-events-none absolute left-2 h-3 w-3 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search tasks…"
          value={filters.search}
          onChange={(e) => onChange({ ...filters, search: e.target.value })}
          className="h-7 w-[180px] rounded-[5px] border border-border bg-surface-2 pl-6 pr-2 font-mono text-[11px] text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
        />
      </div>
      <button
        onClick={() => onChange({ ...filters, overdue: !filters.overdue })}
        className={`h-7 rounded-[5px] border px-2 font-mono text-[11px] transition-colors ${
          filters.overdue
            ? "border-red/50 bg-red/10 text-red"
            : "border-border bg-surface-2 text-muted-foreground hover:bg-surface-3"
        }`}
        title={filters.overdue ? "Show all tasks" : "Show overdue tasks"}
      >
        <AlertCircle className="inline h-3 w-3" />
      </button>
      {[
        { key: "status" as const,   options: STATUS_OPTIONS,   width: "w-[130px]" },
        { key: "priority" as const, options: PRIORITY_OPTIONS, width: "w-[130px]" },
        { key: "taskType" as const, options: TYPE_OPTIONS,     width: "w-[110px]" },
      ].map(({ key, options, width }) => (
        <Select
          key={key}
          value={filters[key]}
          onValueChange={(v) => onChange({ ...filters, [key]: v })}
        >
          <SelectTrigger
            className={`${width} h-7 rounded-[5px] border-border bg-surface-2 font-mono text-[11px] text-muted-foreground`}
          >
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="font-mono text-[11px]">
            {options.map(({ value, label }) => (
              <SelectItem key={value} value={value} className="text-[11px]">
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      ))}
    </div>
  )
}
