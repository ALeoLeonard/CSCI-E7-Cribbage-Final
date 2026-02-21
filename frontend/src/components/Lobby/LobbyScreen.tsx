import { useState } from 'react';
import { useLobbyStore } from '../../store/lobbyStore';

interface LobbyScreenProps {
  onBack: () => void;
}

export function LobbyScreen({ onBack }: LobbyScreenProps) {
  const [name, setName] = useState('Player');
  const [joinCode, setJoinCode] = useState('');
  const { quickMatch, createPrivate, joinPrivate, status, joinCode: createdCode, error, disconnect } = useLobbyStore();

  if (status === 'waiting' || status === 'connecting') {
    return (
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="bg-black/30 backdrop-blur-sm rounded-2xl p-8 max-w-sm w-full text-center border border-white/10">
          <div className="text-4xl mb-4 animate-pulse">⏳</div>
          <h2 className="text-2xl font-bold mb-2">
            {createdCode ? 'Waiting for opponent' : 'Finding match...'}
          </h2>
          {createdCode && (
            <div className="my-4">
              <p className="text-sm opacity-70 mb-2">Share this code:</p>
              <div className="text-4xl font-bold tracking-widest text-gold bg-black/30 rounded-xl py-3">
                {createdCode}
              </div>
            </div>
          )}
          {error && <p className="text-red-400 text-sm mt-2">{error}</p>}
          <button
            onClick={disconnect}
            className="mt-6 text-sm opacity-70 hover:opacity-100 underline"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex items-center justify-center p-4">
      <div className="bg-black/30 backdrop-blur-sm rounded-2xl p-8 max-w-sm w-full text-center border border-white/10">
        <h2 className="text-3xl font-bold mb-6">Multiplayer</h2>

        <div className="mb-6">
          <label className="block text-sm opacity-70 mb-2">Your Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3
                       text-center text-lg focus:outline-none focus:border-gold transition-colors"
            maxLength={20}
          />
        </div>

        <div className="space-y-3 mb-6">
          <button
            onClick={() => quickMatch(name || 'Player')}
            className="w-full bg-gold text-black font-bold py-3 rounded-xl text-lg
                       hover:bg-yellow-400 active:scale-95 transition-all"
          >
            Quick Match
          </button>
          <button
            onClick={() => createPrivate(name || 'Player')}
            className="w-full bg-white/10 text-white font-bold py-3 rounded-xl text-lg
                       hover:bg-white/20 active:scale-95 transition-all"
          >
            Create Private Game
          </button>
        </div>

        <div className="border-t border-white/10 pt-4">
          <label className="block text-sm opacity-70 mb-2">Join with Code</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
              placeholder="ABC123"
              maxLength={6}
              className="flex-1 bg-white/10 border border-white/20 rounded-xl px-4 py-3
                         text-center text-lg tracking-widest uppercase
                         focus:outline-none focus:border-gold transition-colors"
            />
            <button
              onClick={() => joinPrivate(name || 'Player', joinCode)}
              disabled={joinCode.length < 6}
              className="bg-gold text-black font-bold py-3 px-6 rounded-xl
                         disabled:opacity-40 hover:bg-yellow-400 active:scale-95 transition-all"
            >
              Join
            </button>
          </div>
        </div>

        {error && <p className="text-red-400 text-sm mt-4">{error}</p>}

        <button onClick={onBack} className="mt-6 text-sm opacity-60 hover:opacity-100 underline">
          Back to Menu
        </button>
      </div>
    </div>
  );
}
