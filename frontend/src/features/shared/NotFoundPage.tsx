import { Link } from "react-router-dom"

export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center py-24 gap-3">
      <p className="text-6xl font-bold text-muted-foreground/30">404</p>
      <p className="text-sm text-muted-foreground">Page not found.</p>
      <Link to="/" className="text-sm underline underline-offset-4">
        Go to Dashboard
      </Link>
    </div>
  )
}
