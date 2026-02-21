import { CardBack } from '../Card/CardBack';

interface OpponentHandProps {
  cardCount: number;
}

export function OpponentHand({ cardCount }: OpponentHandProps) {
  return (
    <div className="flex justify-center gap-1">
      {Array.from({ length: cardCount }).map((_, i) => (
        <CardBack key={i} small />
      ))}
    </div>
  );
}
