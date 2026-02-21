import type { Card as CardType } from '../../api/types';
import { isRed, suitSymbol } from '../../utils/cardUtils';

interface CardProps {
  card: CardType;
  selected?: boolean;
  onClick?: () => void;
  disabled?: boolean;
  small?: boolean;
  dealDelay?: number;
}

export function Card({ card, selected, onClick, disabled, small, dealDelay = 0 }: CardProps) {
  const red = isRed(card.suit);
  const color = red ? 'text-card-red' : 'text-card-black';
  const suit = suitSymbol(card.suit);

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      aria-label={`${card.rank} of ${card.suit}`}
      className={`
        relative flex flex-col items-center justify-between
        ${small ? 'w-14 h-20 text-xs' : 'w-[96px] h-[134px] text-base'}
        bg-card-white rounded-xl shadow-lg border-2
        transition-all duration-200 ease-out animate-deal
        ${selected
          ? 'border-gold -translate-y-3 shadow-gold/40 shadow-xl ring-2 ring-gold/50 animate-glow'
          : 'border-gray-200 hover:border-gray-300'
        }
        ${disabled ? 'opacity-70 cursor-default' : 'cursor-pointer active:scale-95 hover:-translate-y-1'}
        ${color}
      `}
      style={{ animationDelay: `${dealDelay}ms` }}
    >
      {/* Top-left corner */}
      <div className={`absolute ${small ? 'top-0.5 left-1' : 'top-1 left-1.5'} flex flex-col items-center leading-none`}>
        <span className="font-bold">{card.rank}</span>
        <span className={small ? 'text-[10px]' : 'text-xs'}>{suit}</span>
      </div>

      {/* Center suit */}
      <div className={`flex items-center justify-center flex-1 ${small ? 'text-xl' : 'text-4xl'}`}>
        {suit}
      </div>

      {/* Bottom-right corner (rotated) */}
      <div className={`absolute ${small ? 'bottom-0.5 right-1' : 'bottom-1 right-1.5'} flex flex-col items-center leading-none rotate-180`}>
        <span className="font-bold">{card.rank}</span>
        <span className={small ? 'text-[10px]' : 'text-xs'}>{suit}</span>
      </div>
    </button>
  );
}
