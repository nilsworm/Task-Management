import { create } from "zustand"

interface AIPanelState {
  isOpen: boolean
  toggle: () => void
}

export const useAIPanelStore = create<AIPanelState>((set, get) => ({
  isOpen: false,
  toggle: () => set({ isOpen: !get().isOpen }),
}))
