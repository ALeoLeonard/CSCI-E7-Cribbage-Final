import type { ScoreBreakdown as BreakdownType } from '../../api/types';

interface ScoreBreakdownProps {
  breakdown: BreakdownType;
  label: string;
}

export function ScoreBreakdown({ breakdown, label }: ScoreBreakdownProps) {
  return (
    <div className="bg-black/30 rounded-xl p-4 max-w-sm mx-auto backdrop-blur-sm">
      <h3 className="text-lg font-bold mb-2 text-center">{label}</h3>
      {breakdown.items.length === 0 ? (
        <p className="text-center opacity-60">No points</p>
      ) : (
        <ul className="space-y-1">
          {breakdown.items.map((item, i) => (
            <li key={i} className="flex justify-between text-sm">
              <span>{item.reason}</span>
              <span className="font-bold text-gold">+{item.points}</span>
            </li>
          ))}
        </ul>
      )}
      <div className="border-t border-white/20 mt-2 pt-2 flex justify-between font-bold">
        <span>Total</span>
        <span className="text-gold">{breakdown.total}</span>
      </div>
    </div>
  );
}
