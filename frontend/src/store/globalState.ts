import { create } from 'zustand';

interface GlobalState {
  token: string | null;
  setToken: (token: string) => void;
  logout: () => void;
}

const useGlobalState = create<GlobalState>((set) => ({
  token: null,
  setToken: (token) => set({ token }),
  logout: () => set({ token: null }),
}));

export default useGlobalState;
