import { Component } from "react"
import type { ReactNode, ErrorInfo } from "react"

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  message: string
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, message: "" }
  }

  static getDerivedStateFromError(error: unknown): State {
    const message = error instanceof Error ? error.message : "Unknown error"
    return { hasError: true, message }
  }

  componentDidCatch(error: unknown, info: ErrorInfo) {
    console.error("[ErrorBoundary]", error, info.componentStack)
  }

  handleReset = () => {
    this.setState({ hasError: false, message: "" })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center gap-4 p-12 text-center">
          <p className="text-lg font-semibold">Something went wrong.</p>
          <p className="text-sm text-muted-foreground">{this.state.message}</p>
          <button
            onClick={this.handleReset}
            className="text-sm underline text-primary hover:opacity-80"
          >
            Try again
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
