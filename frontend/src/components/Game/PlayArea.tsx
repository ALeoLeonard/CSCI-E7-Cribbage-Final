import type { Card as CardType } from '../../api/types';
import { Card } from '../Card/Card';
import { cardKey } from '../../utils/cardUtils';

interface PlayAreaProps {
  playerCards: CardType[];
  opponentCards: CardType[];
  runningTotal: number;
}

export function PlayArea({ playerCards, opponentCards, runningTotal }: PlayAreaProps) {
  const showCount = playerCards.length > 0 || opponentCards.length > 0 || runningTotal > 0;

  return (
    <div className="flex flex-col items-center gap-1 w-full">
      {/* Opponent's played cards — fan above center */}
      <div className="flex justify-center items-end min-h-[103px] sm:min-h-[142px]">
        {opponentCards.map((card, i) => (
          <div
            key={cardKey(card)}
            className={`animate-play-down ${i > 0 ? '-ml-5 sm:-ml-7' : ''}`}
            style={{
              transform: `rotate(${(i - (opponentCards.length - 1) / 2) * 2}deg)`,
              zIndex: i,
            }}
          >
            <Card card={card} disabled />
          </div>
        ))}
        {opponentCards.length === 0 && (
          <div className="h-[95px] sm:h-[134px]" />
        )}
      </div>

      {/* Running count badge */}
      {showCount && (
        <div className="text-sm sm:text-base font-bold bg-black/30 px-4 sm:px-5 py-1 rounded-full">
          Count: {runningTotal} / 31
        </div>
      )}

      {/* Player's played cards — fan below center */}
      <div className="flex justify-center items-start min-h-[103px] sm:min-h-[142px]">
        {playerCards.map((card, i) => (
          <div
            key={cardKey(card)}
            className={`animate-play-up ${i > 0 ? '-ml-5 sm:-ml-7' : ''}`}
            style={{
              transform: `rotate(${(i - (playerCards.length - 1) / 2) * -2}deg)`,
              zIndex: i,
            }}
          >
            <Card card={card} disabled />
          </div>
        ))}
        {playerCards.length === 0 && (
          <div className="h-[95px] sm:h-[134px]" />
        )}
      </div>
    </div>
  );
}
