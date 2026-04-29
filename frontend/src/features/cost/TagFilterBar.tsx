import { cn } from "@/lib/utils"

interface Props {
  availableTags: string[]
  selectedTags: string[]
  onChange: (tags: string[]) => void
}

export function TagFilterBar({ availableTags, selectedTags, onChange }: Props) {
  if (availableTags.length === 0) return null

  function toggle(tag: string) {
    if (selectedTags.includes(tag)) {
      onChange(selectedTags.filter((t) => t !== tag))
    } else {
      onChange([...selectedTags, tag])
    }
  }

  return (
    <div className="flex flex-wrap gap-2">
      {availableTags.map((tag) => {
        const active = selectedTags.includes(tag)
        return (
          <button
            key={tag}
            onClick={() => toggle(tag)}
            className={cn(
              "rounded-full border px-3 py-0.5 text-xs font-medium transition-colors",
              active
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border bg-background text-muted-foreground hover:border-primary hover:text-foreground",
            )}
          >
            {tag}
          </button>
        )
      })}
      {selectedTags.length > 0 && (
        <button
          onClick={() => onChange([])}
          className="rounded-full border border-border px-3 py-0.5 text-xs text-muted-foreground hover:text-foreground"
        >
          Zurücksetzen
        </button>
      )}
    </div>
  )
}
