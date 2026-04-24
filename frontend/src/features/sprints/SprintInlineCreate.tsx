import { useState } from "react"
import { X } from "lucide-react"
import { useCreateTask } from "@/api/hooks/tasks"
import { toast } from "sonner"

interface Props {
  sprintId: string
  onDone: () => void
}

export function SprintInlineCreate({ sprintId, onDone }: Props) {
  const [title, setTitle] = useState("")
  const create = useCreateTask()

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!title.trim()) return
    create.mutate(
      {
        task_type: "sprint",
        title: title.trim(),
        priority: "medium",
        estimation: null,
        tags: [],
        sprint_id: sprintId,
      },
      {
        onSuccess: () => {
          toast.success("Task created")
          onDone()
        },
        onError: () => toast.error("Failed to create task"),
      },
    )
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-center gap-2 rounded-[5px] border border-cyan/30 bg-surface-2 px-3 py-2"
    >
      <input
        autoFocus
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        onKeyDown={(e) => e.key === "Escape" && onDone()}
        placeholder="New task title…"
        className="flex-1 bg-transparent font-mono text-[11px] text-foreground outline-none placeholder:text-muted-foreground/50"
      />
      <button
        type="submit"
        disabled={!title.trim() || create.isPending}
        className="h-6 rounded-[4px] bg-cyan px-2.5 font-mono text-[10px] font-bold text-black disabled:opacity-50"
      >
        {create.isPending ? "…" : "Create"}
      </button>
      <button
        type="button"
        onClick={onDone}
        className="flex h-6 w-6 items-center justify-center rounded-[4px] border border-border text-muted-foreground transition-colors hover:text-foreground"
      >
        <X className="h-3 w-3" />
      </button>
    </form>
  )
}
