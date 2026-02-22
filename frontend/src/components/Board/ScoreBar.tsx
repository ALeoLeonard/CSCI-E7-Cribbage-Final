interface ScoreBarProps {
  playerScore: number;
  opponentScore: number;
  playerName: string;
  opponentName: string;
  playerIsDealer: boolean;
  roundNumber: number;
}

export function ScoreBar({
  playerScore,
  opponentScore,
  playerName,
  opponentName,
  playerIsDealer,
  roundNumber,
}: ScoreBarProps) {
  return (
    <div className="flex items-center justify-between bg-black/20 rounded-xl px-3 py-1.5 text-xs gap-2">
      {/* Player score */}
      <div className="flex items-center gap-1.5 min-w-0">
        <span className="w-2 h-2 rounded-full bg-blue-400 shrink-0" />
        <span className="font-bold text-blue-300 truncate">{playerName}</span>
        {playerIsDealer && (
          <span className="text-[9px] bg-gold/20 text-gold px-1 rounded-full shrink-0">D</span>
        )}
        <span className="font-bold text-blue-200">{playerScore}</span>
      </div>

      {/* Round indicator */}
      <span className="opacity-40 shrink-0">R{roundNumber}</span>

      {/* Opponent score */}
      <div className="flex items-center gap-1.5 min-w-0">
        <span className="font-bold text-red-200">{opponentScore}</span>
        {!playerIsDealer && (
          <span className="text-[9px] bg-gold/20 text-gold px-1 rounded-full shrink-0">D</span>
        )}
        <span className="font-bold text-red-300 truncate">{opponentName}</span>
        <span className="w-2 h-2 rounded-full bg-red-400 shrink-0" />
      </div>
    </div>
  );
}
