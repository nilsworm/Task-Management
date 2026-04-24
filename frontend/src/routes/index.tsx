import { createBrowserRouter } from "react-router-dom"
import { AppLayout } from "@/layouts/AppLayout"
import { DashboardPage } from "@/features/dashboard/DashboardPage"
import { TasksPage } from "@/features/tasks/TasksPage"
import { SprintsPage } from "@/features/sprints/SprintsPage"
import { SprintDetailPage } from "@/features/sprints/SprintDetailPage"
import { GoalsPage } from "@/features/goals/GoalsPage"
import { GoalDetailPage } from "@/features/goals/GoalDetailPage"
import { NotFoundPage } from "@/features/shared/NotFoundPage"

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "tasks", element: <TasksPage /> },
      { path: "sprints", element: <SprintsPage /> },
      { path: "sprints/:id", element: <SprintDetailPage /> },
      { path: "goals", element: <GoalsPage /> },
      { path: "goals/:id", element: <GoalDetailPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
])
