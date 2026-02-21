import { create } from 'zustand';

interface SoundStore {
  enabled: boolean;
  toggle: () => void;
}

export const useSoundStore = create<SoundStore>((set) => ({
  enabled: typeof window !== 'undefined'
    ? localStorage.getItem('soundEnabled') !== 'false'
    : true,
  toggle: () =>
    set((s) => {
      const next = !s.enabled;
      localStorage.setItem('soundEnabled', String(next));
      return { enabled: next };
    }),
}));
