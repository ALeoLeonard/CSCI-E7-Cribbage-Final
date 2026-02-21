import { useEffect, useRef, useState } from 'react';
import { useGameStore } from '../../store/gameStore';
import { CardFan } from '../Card/CardFan';
import { CribbageBoard } from '../Board/CribbageBoard';
import { OpponentHand } from './OpponentHand';
import { StarterCard } from './StarterCard';
import { PlayArea } from './PlayArea';
import { ScoreBreakdown } from './ScoreBreakdown';
import { GameOverModal } from './GameOverModal';
import type { Card as CardType } from '../../api/types';

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

  const [floatingScore, setFloatingScore] = useState<{ text: string; key: number } | null>(null);

  // Track which cards belong to player vs opponent in the play pile
  const [playerPlayed, setPlayerPlayed] = useState<CardType[]>([]);
  const [opponentPlayed, setOpponentPlayed] = useState<CardType[]>([]);
  const prevPileLenRef = useRef(0);

  // Show floating score when last_action has score events
  useEffect(() => {
    if (game?.last_action?.score_events?.length) {
      const total = game.last_action.score_events.reduce((s, e) => s + e.points, 0);
      if (total > 0) {
        setFloatingScore({ text: `+${total}`, key: Date.now() });
        const timer = setTimeout(() => setFloatingScore(null), 1500);
        return () => clearTimeout(timer);
      }
    }
  }, [game?.last_action]);

  // Attribute play_pile cards to player/opponent
  useEffect(() => {
    if (!game) return;
    const pile = game.play_pile;
    const prevLen = prevPileLenRef.current;

    if (pile.length === 0) {
      setPlayerPlayed([]);
      setOpponentPlayed([]);
    } else if (pile.length > prevLen) {
      const newCard = pile[pile.length - 1];
      const actor = game.last_action?.actor;
      if (actor === game.opponent.name) {
        setOpponentPlayed((prev) => [...prev, newCard]);
      } else {
        setPlayerPlayed((prev) => [...prev, newCard]);
      }
    }

    prevPileLenRef.current = pile.length;
  }, [game?.play_pile.length, game?.last_action]);

  // Reset card attribution on phase change away from play
  useEffect(() => {
    if (game?.phase !== 'play') {
      setPlayerPlayed([]);
      setOpponentPlayed([]);
      prevPileLenRef.current = 0;
    }
  }, [game?.phase]);

  if (!game) return null;

  const { phase, player, opponent, starter, running_total, last_action, score_breakdown, winner } = game;

  const canPlay = (cardIndex: number) =>
    phase === 'play' && player.hand[cardIndex]?.value + running_total <= 31;

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

  return (
    <div className="grid grid-cols-[2fr_3fr] flex-1 min-h-0 w-full px-2 pt-1 pb-1 gap-3 relative">
      {/* Floating score animation */}
      {floatingScore && (
        <div
          key={floatingScore.key}
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50
                     text-4xl font-bold text-gold animate-score-float pointer-events-none"
        >
          {floatingScore.text}
        </div>
      )}

      {/* ===== LEFT COLUMN: Board side ===== */}
      <div className="flex flex-col items-center justify-center gap-3 min-h-0">
        <CribbageBoard
          playerScore={player.score}
          opponentScore={opponent.score}
          playerName={player.name}
          opponentName={opponent.name}
          playerIsDealer={player.is_dealer}
        />

        {/* Starter + Crib below board */}
        <div className="flex items-center justify-center gap-4">
          <StarterCard card={starter} />
          {phase === 'discard' && (
            <div className="flex flex-col items-center gap-1">
              <span className="text-xs opacity-60">
                {player.is_dealer ? player.name : opponent.name}'s Crib
              </span>
              <div className="w-[96px] h-[134px] rounded-xl border-2 border-dashed border-white/30 flex items-center justify-center text-white/40 text-sm">
                {game.crib_count}/4
              </div>
            </div>
          )}
        </div>

        {/* Round indicator */}
        <span className="text-xs opacity-40">Round {game.round_number}</span>
      </div>

      {/* ===== RIGHT COLUMN: Card play side ===== */}
      <div className="grid grid-rows-[auto_1fr_auto] min-h-0 gap-1">
        {/* Opponent zone */}
        <div className="flex items-center justify-between px-1 py-1">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-sm font-bold text-red-300 truncate">
              {opponent.name}
            </span>
            {!player.is_dealer && (
              <span className="text-[10px] bg-gold/20 text-gold px-1.5 rounded-full">D</span>
            )}
          </div>
          <OpponentHand cardCount={opponent.hand_count} />
        </div>

        {/* Middle: play area / score breakdown */}
        <div key={phase} className="flex flex-col items-center justify-center gap-1 min-h-0 overflow-hidden animate-phase-enter">
          {phase === 'play' && (
            <PlayArea
              playerCards={playerPlayed}
              opponentCards={opponentPlayed}
              runningTotal={running_total}
            />
          )}

          {/* Score breakdown during counting */}
          {score_breakdown && (phase === 'count_non_dealer' || phase === 'count_dealer' || phase === 'count_crib') && (
            <ScoreBreakdown breakdown={score_breakdown} label={last_action?.message || 'Score'} />
          )}

          {/* Last action message during play */}
          {last_action && phase === 'play' && (
            <div className="text-center bg-black/20 rounded-lg px-4 py-1.5 text-sm animate-slide-in max-w-xs">
              <span className="font-medium">{last_action.message}</span>
              {last_action.score_events.map((e, i) => (
                <span key={i} className="text-gold ml-2 font-bold">+{e.points}</span>
              ))}
            </div>
          )}
        </div>

        {/* Player zone */}
        <div className="flex flex-col gap-0.5">
          {/* Phase badge + action button */}
          <div className="flex items-center justify-center gap-3 min-h-[40px]">
            <span className="bg-black/20 rounded-full px-3 py-1 text-sm font-medium inline-flex items-center gap-1.5">
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
                className="bg-gold text-black font-bold py-2 px-6 rounded-xl
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
                className="bg-red-600 text-white font-bold py-2 px-6 rounded-xl
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
                className="bg-gold text-black font-bold py-2 px-6 rounded-xl
                           hover:bg-yellow-400 active:scale-95 transition-all
                           shadow-lg shadow-gold/30"
              >
                {phase === 'count_crib' ? 'Next Round' : 'Continue'}
              </button>
            )}
          </div>

          {error && (
            <div className="text-red-300 text-center text-sm bg-red-900/40 rounded-lg px-3 py-1 animate-slide-in">
              {error}
            </div>
          )}

          <CardFan
            cards={player.hand}
            selectedIndices={phase === 'discard' ? selectedIndices : []}
            onCardClick={(i) => {
              if (phase === 'discard') {
                toggleSelect(i);
              } else if (phase === 'play' && canPlay(i)) {
                playCard(i);
              }
            }}
            disabled={loading}
          />
        </div>
      </div>

      {/* Game over modal */}
      {winner && (
        <GameOverModal
          winner={winner}
          playerName={player.name}
          playerScore={player.score}
          opponentScore={opponent.score}
          onNewGame={() => newGame(player.name)}
        />
      )}
    </div>
  );
}
