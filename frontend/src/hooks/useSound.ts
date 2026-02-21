import { useCallback, useRef } from 'react';

// Web Audio API sound synthesizer — no external audio files needed
const audioCtx = typeof window !== 'undefined' ? new (window.AudioContext || (window as any).webkitAudioContext)() : null;

function playTone(frequency: number, duration: number, type: OscillatorType = 'sine', volume = 0.15) {
  if (!audioCtx) return;
  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();
  osc.type = type;
  osc.frequency.setValueAtTime(frequency, audioCtx.currentTime);
  gain.gain.setValueAtTime(volume, audioCtx.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
  osc.connect(gain);
  gain.connect(audioCtx.destination);
  osc.start();
  osc.stop(audioCtx.currentTime + duration);
}

function playNoise(duration: number, volume = 0.05) {
  if (!audioCtx) return;
  const bufferSize = audioCtx.sampleRate * duration;
  const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
  const data = buffer.getChannelData(0);
  for (let i = 0; i < bufferSize; i++) {
    data[i] = Math.random() * 2 - 1;
  }
  const source = audioCtx.createBufferSource();
  const gain = audioCtx.createGain();
  const filter = audioCtx.createBiquadFilter();
  filter.type = 'lowpass';
  filter.frequency.value = 2000;
  source.buffer = buffer;
  gain.gain.setValueAtTime(volume, audioCtx.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
  source.connect(filter);
  filter.connect(gain);
  gain.connect(audioCtx.destination);
  source.start();
}

export const sounds = {
  cardPlay: () => {
    playNoise(0.08, 0.1);
    playTone(800, 0.05, 'sine', 0.05);
  },
  shuffle: () => {
    for (let i = 0; i < 5; i++) {
      setTimeout(() => playNoise(0.06, 0.06), i * 40);
    }
  },
  fifteen: () => {
    playTone(523, 0.15, 'sine', 0.12);
    setTimeout(() => playTone(659, 0.15, 'sine', 0.12), 100);
  },
  thirtyOne: () => {
    playTone(523, 0.12, 'sine', 0.12);
    setTimeout(() => playTone(659, 0.12, 'sine', 0.12), 80);
    setTimeout(() => playTone(784, 0.2, 'sine', 0.12), 160);
  },
  go: () => {
    playTone(300, 0.2, 'triangle', 0.1);
  },
  win: () => {
    const notes = [523, 659, 784, 1047];
    notes.forEach((freq, i) => {
      setTimeout(() => playTone(freq, 0.3, 'sine', 0.15), i * 150);
    });
  },
  lose: () => {
    playTone(400, 0.3, 'sawtooth', 0.08);
    setTimeout(() => playTone(350, 0.4, 'sawtooth', 0.06), 200);
  },
  score: () => {
    playTone(660, 0.1, 'sine', 0.1);
  },
  tap: () => {
    playTone(600, 0.04, 'sine', 0.08);
  },
};

export function ensureAudioReady() {
  if (audioCtx?.state === 'suspended') {
    audioCtx.resume();
  }
}

export function useSound() {
  const enabled = useRef(
    typeof window !== 'undefined'
      ? localStorage.getItem('soundEnabled') !== 'false'
      : true
  );

  const toggle = useCallback(() => {
    enabled.current = !enabled.current;
    localStorage.setItem('soundEnabled', String(enabled.current));
  }, []);

  const play = useCallback((sound: keyof typeof sounds) => {
    if (enabled.current && audioCtx) {
      // Resume AudioContext on user interaction (mobile requirement)
      if (audioCtx.state === 'suspended') {
        audioCtx.resume();
      }
      sounds[sound]();
    }
  }, []);

  return { play, toggle, isEnabled: () => enabled.current };
}
