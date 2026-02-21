import type { Card as CardType } from '../../api/types';
import { Card } from './Card';
import { cardKey } from '../../utils/cardUtils';

interface CardFanProps {
  cards: CardType[];
  selectedIndices?: number[];
  onCardClick?: (index: number) => void;
  disabled?: boolean;
}

export function CardFan({ cards, selectedIndices = [], onCardClick, disabled }: CardFanProps) {
  return (
    <div className="flex justify-center gap-1.5 flex-wrap px-2">
      {cards.map((card, i) => (
        <Card
          key={cardKey(card)}
          card={card}
          selected={selectedIndices.includes(i)}
          onClick={() => onCardClick?.(i)}
          disabled={disabled}
          dealDelay={i * 80}
        />
      ))}
    </div>
  );
}
