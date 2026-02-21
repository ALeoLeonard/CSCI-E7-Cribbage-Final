import type { Card as CardType } from '../../api/types';
import { Card } from '../Card/Card';
import { CardBack } from '../Card/CardBack';

interface StarterCardProps {
  card?: CardType;
}

export function StarterCard({ card }: StarterCardProps) {
  return (
    <div className="flex flex-col items-center gap-1">
      <span className="text-xs opacity-60">Starter</span>
      {card ? <Card card={card} disabled /> : <CardBack />}
    </div>
  );
}
