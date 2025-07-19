import { create } from 'zustand';

interface GlobalState {
  token: string | null;
  darkMode: boolean;
  setToken: (token: string) => void;
  toggleDarkMode: () => void;
  logout: () => void;
}

const useGlobalState = create<GlobalState>((set) => ({
  token: null,
  darkMode: false,
  setToken: (token) => set({ token }),
  toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),
  logout: () => set({ token: null }),
}));

export default useGlobalState;
