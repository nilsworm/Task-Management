import { execSync } from "child_process"
import * as path from "path"

export default async function globalSetup() {
  try {
    const res = await fetch("http://localhost:8000/health")
    if (!res.ok) {
      console.warn("⚠  Backend returned non-200 — skipping seed")
      return
    }
  } catch {
    console.warn("⚠  Backend not reachable at http://localhost:8000 — skipping seed")
    return
  }

  // process.cwd() is the frontend/ directory when running `pnpm playwright test`
  const backendDir = path.resolve(process.cwd(), "../backend")
  console.log("▶  Seeding test data (--reset)…")
  try {
    execSync("uv run python -m scripts.seed --reset", {
      cwd: backendDir,
      stdio: "inherit",
      timeout: 60_000,
    })
    console.log("✓  Seed complete")
  } catch (err) {
    console.error("✕  Seed failed:", err)
    process.exit(1)
  }
}
