interface GameOverModalProps {
  winner: string;
  playerName: string;
  playerScore: number;
  opponentScore: number;
  onNewGame: () => void;
}

export function GameOverModal({
  winner,
  playerName,
  playerScore,
  opponentScore,
  onNewGame,
}: GameOverModalProps) {
  const isWin = winner === playerName;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 backdrop-blur-sm p-4">
      <div className="bg-felt-dark rounded-2xl p-8 max-w-sm w-full text-center shadow-2xl border border-white/10">
        <div className="text-6xl mb-4">{isWin ? '🏆' : '😞'}</div>
        <h2 className="text-3xl font-bold mb-2">
          {isWin ? 'You Win!' : 'You Lose!'}
        </h2>
        <p className="text-lg opacity-80 mb-4">
          {winner} wins the game!
        </p>
        <div className="flex justify-center gap-8 mb-6">
          <div>
            <div className="text-sm opacity-60">You</div>
            <div className="text-2xl font-bold">{playerScore}</div>
          </div>
          <div>
            <div className="text-sm opacity-60">Computer</div>
            <div className="text-2xl font-bold">{opponentScore}</div>
          </div>
        </div>
        <button
          onClick={onNewGame}
          className="bg-gold text-black font-bold py-3 px-8 rounded-xl text-lg
                     hover:bg-yellow-400 active:scale-95 transition-all"
        >
          Play Again
        </button>
      </div>
    </div>
  );
}
