import { create } from 'zustand';

interface GlobalState {
  token: string | null;
  setToken: (token: string) => void;
  clearToken: () => void;
}

const useGlobalState = create<GlobalState>((set) => ({
  token: null,
  setToken: (token) => set({ token }),
  clearToken: () => set({ token: null }),
}));

export default useGlobalState;
