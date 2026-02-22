import { useGameStore } from '../../store/gameStore';
import { BoardLayout } from './BoardLayout';

export function GameBoard() {
  const {
    game,
    loading,
    error,
    selectedIndices,
    toggleSelect,
    discard,
    playCard,
    sayGo,
    acknowledge,
    newGame,
  } = useGameStore();

  if (!game) return null;

  const { phase, player, opponent, running_total } = game;

  const canPlay = (i: number) =>
    phase === 'play' && player.hand[i]?.value + running_total <= 31;

  const hasPlayableCard = phase === 'play' &&
    player.hand.some((c) => c.value + running_total <= 31);

  const phaseLabel = (): string => {
    switch (phase) {
      case 'discard': return `Select 2 for crib`;
      case 'play': return hasPlayableCard ? 'Tap a card to play' : "No plays — say Go";
      case 'count_non_dealer': return `Counting ${player.is_dealer ? opponent.name : player.name}'s hand`;
      case 'count_dealer': return `Counting ${player.is_dealer ? player.name : opponent.name}'s hand`;
      case 'count_crib': return `Counting ${player.is_dealer ? player.name : opponent.name}'s crib`;
      case 'game_over': return 'Game Over';
    }
  };

  const phaseIcon = (): string => {
    switch (phase) {
      case 'discard': return '🤔';
      case 'play': return '🎯';
      case 'count_non_dealer':
      case 'count_dealer':
      case 'count_crib': return '📊';
      case 'game_over': return '🏁';
    }
  };

  const actionBar = (
    <>
      <span className="bg-black/20 rounded-full px-2 sm:px-3 py-0.5 sm:py-1 text-xs sm:text-sm font-medium inline-flex items-center gap-1 sm:gap-1.5">
        <span>{phaseIcon()}</span>
        <span>{phaseLabel()}</span>
        {phase === 'discard' && (
          <span className="opacity-60">({selectedIndices.length}/2)</span>
        )}
      </span>

      {phase === 'discard' && (
        <button
          onClick={discard}
          disabled={loading || selectedIndices.length !== 2}
          className="bg-gold text-black font-bold py-1.5 sm:py-2 px-4 sm:px-6 rounded-xl text-sm sm:text-base
                     disabled:opacity-40 disabled:cursor-not-allowed
                     hover:bg-yellow-400 active:scale-95 transition-all
                     shadow-lg shadow-gold/30"
        >
          {loading ? '...' : 'Send to Crib'}
        </button>
      )}

      {phase === 'play' && !hasPlayableCard && (
        <button
          onClick={sayGo}
          disabled={loading}
          className="bg-red-600 text-white font-bold py-1.5 sm:py-2 px-4 sm:px-6 rounded-xl text-sm sm:text-base
                     hover:bg-red-500 active:scale-95 transition-all
                     shadow-lg shadow-red-600/30 animate-glow"
        >
          Say Go!
        </button>
      )}

      {(phase === 'count_non_dealer' || phase === 'count_dealer' || phase === 'count_crib') && (
        <button
          onClick={acknowledge}
          disabled={loading}
          className="bg-gold text-black font-bold py-1.5 sm:py-2 px-4 sm:px-6 rounded-xl text-sm sm:text-base
                     hover:bg-yellow-400 active:scale-95 transition-all
                     shadow-lg shadow-gold/30"
        >
          {phase === 'count_crib' ? 'Next Round' : 'Continue'}
        </button>
      )}
    </>
  );

  return (
    <BoardLayout
      game={game}
      error={error}
      selectedIndices={selectedIndices}
      loading={loading}
      actionBar={actionBar}
      onCardClick={(i) => {
        if (phase === 'discard') toggleSelect(i);
        else if (phase === 'play' && canPlay(i)) playCard(i);
      }}
      onNewGame={() => newGame(player.name)}
    />
  );
}
