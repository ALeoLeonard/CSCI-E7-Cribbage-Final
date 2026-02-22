import { useEffect } from 'react';
import { useStatsStore } from '../../store/statsStore';

interface StatsScreenProps {
  playerName: string;
  onBack: () => void;
}

export function StatsScreen({ playerName, onBack }: StatsScreenProps) {
  const { stats, loading, loadStats } = useStatsStore();

  useEffect(() => {
    loadStats(playerName);
  }, [playerName, loadStats]);

  if (!stats) return null;

  const streakLabel =
    stats.current_streak > 0
      ? `${stats.current_streak}W`
      : stats.current_streak < 0
        ? `${Math.abs(stats.current_streak)}L`
        : '-';

  return (
    <div className="flex-1 flex items-center justify-center p-4">
      <div className="bg-black/30 backdrop-blur-sm rounded-2xl p-8 max-w-sm w-full border border-white/10">
        <button
          onClick={onBack}
          className="text-sm opacity-60 hover:opacity-100 mb-4 transition-opacity"
        >
          &larr; Back to Menu
        </button>

        <h2 className="text-2xl font-bold mb-1 text-center">Statistics</h2>
        <p className="text-sm opacity-60 text-center mb-6">{stats.player_name}</p>

        {stats.games === 0 ? (
          <p className="text-center opacity-60 py-8">No games played yet. Go play some cribbage!</p>
        ) : (
          <>
            {/* Win/Loss Summary */}
            <div className="grid grid-cols-3 gap-3 mb-6">
              <div className="bg-white/5 rounded-xl p-3 text-center">
                <div className="text-2xl font-bold">{stats.games}</div>
                <div className="text-xs opacity-60">Games</div>
              </div>
              <div className="bg-white/5 rounded-xl p-3 text-center">
                <div className="text-2xl font-bold text-green-400">{stats.wins}</div>
                <div className="text-xs opacity-60">Wins</div>
              </div>
              <div className="bg-white/5 rounded-xl p-3 text-center">
                <div className="text-2xl font-bold text-red-400">{stats.losses}</div>
                <div className="text-xs opacity-60">Losses</div>
              </div>
            </div>

            {/* Win Rate Bar */}
            <div className="mb-6">
              <div className="flex justify-between text-sm mb-1">
                <span className="opacity-60">Win Rate</span>
                <span className="font-bold text-gold">{stats.win_rate}%</span>
              </div>
              <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gold rounded-full transition-all duration-500"
                  style={{ width: `${stats.win_rate}%` }}
                />
              </div>
            </div>

            {/* Scoring Stats */}
            <div className="grid grid-cols-2 gap-3 mb-6">
              <div className="bg-white/5 rounded-xl p-3 text-center">
                <div className="text-lg font-bold">{stats.avg_hand_score}</div>
                <div className="text-xs opacity-60">Avg Hand</div>
              </div>
              <div className="bg-white/5 rounded-xl p-3 text-center">
                <div className="text-lg font-bold">{stats.avg_crib_score}</div>
                <div className="text-xs opacity-60">Avg Crib</div>
              </div>
              <div className="bg-white/5 rounded-xl p-3 text-center">
                <div className="text-lg font-bold text-gold">{stats.best_hand}</div>
                <div className="text-xs opacity-60">Best Hand</div>
              </div>
              <div className="bg-white/5 rounded-xl p-3 text-center">
                <div className="text-lg font-bold">{stats.total_points.toLocaleString()}</div>
                <div className="text-xs opacity-60">Total Pts</div>
              </div>
            </div>

            {/* Streaks */}
            <div className="grid grid-cols-2 gap-3 mb-6">
              <div className="bg-white/5 rounded-xl p-3 text-center">
                <div className="text-lg font-bold">{streakLabel}</div>
                <div className="text-xs opacity-60">Current Streak</div>
              </div>
              <div className="bg-white/5 rounded-xl p-3 text-center">
                <div className="text-lg font-bold text-gold">{stats.best_win_streak}</div>
                <div className="text-xs opacity-60">Best Streak</div>
              </div>
            </div>

            {/* Per-Difficulty Breakdown */}
            {stats.per_difficulty.length > 0 && (
              <div>
                <h3 className="text-sm font-bold opacity-60 mb-2">By Difficulty</h3>
                <div className="space-y-2">
                  {stats.per_difficulty.map((d) => (
                    <div
                      key={d.difficulty}
                      className="bg-white/5 rounded-xl px-4 py-2 flex items-center justify-between"
                    >
                      <span className="capitalize font-medium">{d.difficulty}</span>
                      <span className="text-sm opacity-80">
                        {d.wins}-{d.losses}{' '}
                        <span className="text-gold">({d.win_rate}%)</span>
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {loading && (
          <p className="text-xs text-center opacity-40 mt-4">Syncing with server...</p>
        )}
      </div>
    </div>
  );
}
