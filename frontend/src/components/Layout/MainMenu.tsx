import { useState } from 'react';
import { useGameStore } from '../../store/gameStore';
import type { AIDifficulty } from '../../api/types';

interface MainMenuProps {
  onMultiplayer?: () => void;
  onStats?: () => void;
  playerName?: string;
  onNameChange?: (name: string) => void;
}

export function MainMenu({ onMultiplayer, onStats, playerName, onNameChange }: MainMenuProps) {
  const [name, setName] = useState(playerName || 'Player');
  const { newGame, loading, difficulty, setDifficulty } = useGameStore();

  const handleNameChange = (value: string) => {
    setName(value);
    onNameChange?.(value);
  };

  const difficulties: { value: AIDifficulty; label: string; desc: string }[] = [
    { value: 'easy', label: 'Easy', desc: 'Random play' },
    { value: 'medium', label: 'Medium', desc: 'Smart discards' },
    { value: 'hard', label: 'Hard', desc: 'Full strategy' },
  ];

  return (
    <div className="flex-1 flex items-center justify-center p-4">
      <div className="bg-black/30 backdrop-blur-sm rounded-2xl p-8 max-w-sm w-full text-center border border-white/10">
        <div className="text-6xl mb-4">🃏</div>
        <h1 className="text-4xl font-bold mb-2">Cribbage</h1>
        <p className="text-sm opacity-60 mb-8">First to 121 wins</p>

        <div className="mb-6">
          <label className="block text-sm opacity-70 mb-2">Your Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => handleNameChange(e.target.value)}
            className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3
                       text-center text-lg focus:outline-none focus:border-gold
                       transition-colors"
            maxLength={20}
          />
        </div>

        <div className="mb-8">
          <label className="block text-sm opacity-70 mb-2">AI Difficulty</label>
          <div className="grid grid-cols-3 gap-2">
            {difficulties.map((d) => (
              <button
                key={d.value}
                onClick={() => setDifficulty(d.value)}
                className={`
                  py-2 px-3 rounded-xl text-sm font-medium transition-all
                  ${difficulty === d.value
                    ? 'bg-gold text-black'
                    : 'bg-white/10 hover:bg-white/20'
                  }
                `}
              >
                <div>{d.label}</div>
                <div className="text-xs opacity-60">{d.desc}</div>
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <button
            onClick={() => newGame(name || 'Player')}
            disabled={loading}
            className="w-full bg-gold text-black font-bold py-4 rounded-xl text-xl
                       hover:bg-yellow-400 active:scale-95 transition-all
                       disabled:opacity-50 shadow-lg shadow-gold/30"
          >
            {loading ? 'Starting...' : 'Play vs Computer'}
          </button>

          {onMultiplayer && (
            <button
              onClick={onMultiplayer}
              className="w-full bg-white/10 text-white font-bold py-4 rounded-xl text-xl
                         hover:bg-white/20 active:scale-95 transition-all"
            >
              Multiplayer
            </button>
          )}

          {onStats && (
            <button
              onClick={onStats}
              className="w-full bg-white/10 text-white font-bold py-3 rounded-xl text-lg
                         hover:bg-white/20 active:scale-95 transition-all"
            >
              Statistics
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
