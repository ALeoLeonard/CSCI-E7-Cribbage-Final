import { useEffect, useRef, useState, type ReactNode } from 'react';
import { CardFan } from '../Card/CardFan';
import { CribbageBoard } from '../Board/CribbageBoard';
import { ScoreBar } from '../Board/ScoreBar';
import { OpponentHand } from './OpponentHand';
import { StarterCard } from './StarterCard';
import { PlayArea } from './PlayArea';
import { ScoreBreakdown } from './ScoreBreakdown';
import { GameOverModal } from './GameOverModal';
import type { Card as CardType, GameState } from '../../api/types';

function suitSymbol(suit: string): string {
  switch (suit) {
    case 'Hearts': return '♥';
    case 'Diamonds': return '♦';
    case 'Clubs': return '♣';
    case 'Spades': return '♠';
    default: return '';
  }
}

interface BoardLayoutProps {
  game: GameState;
  error: string | null;
  selectedIndices: number[];
  loading?: boolean;
  /** Whether it's currently this player's turn. Defaults to true (single-player). */
  yourTurn?: boolean;
  /** Content rendered in the action bar area (phase badge, buttons, etc.) */
  actionBar: ReactNode;
  /** Content rendered below the error area (e.g. disconnect button) */
  errorExtra?: ReactNode;
  /** Content rendered after the game over modal (e.g. ChatBubble) */
  extras?: ReactNode;
  onCardClick: (index: number) => void;
  onNewGame: () => void;
}

export function BoardLayout({
  game,
  error,
  selectedIndices,
  loading,
  yourTurn = true,
  actionBar,
  errorExtra,
  extras,
  onCardClick,
  onNewGame,
}: BoardLayoutProps) {
  const [floatingScore, setFloatingScore] = useState<{ text: string; key: number } | null>(null);
  const [playerPlayed, setPlayerPlayed] = useState<CardType[]>([]);
  const [opponentPlayed, setOpponentPlayed] = useState<CardType[]>([]);
  const prevPileLenRef = useRef(0);

  const { phase, player, opponent, starter, running_total, last_action, score_breakdown, winner } = game;

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

  return (
    <div className="flex flex-col sm:grid sm:grid-cols-[2fr_3fr] flex-1 min-h-0 w-full px-2 pt-1 pb-1 gap-1 sm:gap-3 relative">
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

      {/* ===== Mobile: compact score bar ===== */}
      <div className="sm:hidden px-1">
        <ScoreBar
          playerScore={player.score}
          opponentScore={opponent.score}
          playerName={player.name}
          opponentName={opponent.name}
          playerIsDealer={player.is_dealer}
          roundNumber={game.round_number}
        />
      </div>

      {/* ===== Desktop: LEFT COLUMN — Board side ===== */}
      <div className="hidden sm:flex flex-col items-center justify-center gap-3 min-h-0">
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

      {/* ===== RIGHT COLUMN (desktop) / MAIN CONTENT (mobile) ===== */}
      <div className="grid grid-rows-[auto_1fr_auto] min-h-0 gap-0.5 sm:gap-1 flex-1">
        {/* Opponent zone */}
        <div className="flex items-center justify-between px-1 py-0.5 sm:py-1">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-sm font-bold text-red-300 truncate">
              {opponent.name}
            </span>
            {!player.is_dealer && (
              <span className="text-[10px] bg-gold/20 text-gold px-1.5 rounded-full">D</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {starter && (
              <div className="sm:hidden flex items-center gap-1">
                <span className="text-[10px] opacity-50">Cut:</span>
                <span className="text-xs font-bold">{starter.rank}{suitSymbol(starter.suit)}</span>
              </div>
            )}
            <OpponentHand cardCount={opponent.hand_count} />
          </div>
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

          {score_breakdown && (phase === 'count_non_dealer' || phase === 'count_dealer' || phase === 'count_crib') && (
            <ScoreBreakdown breakdown={score_breakdown} label={last_action?.message || 'Score'} />
          )}

          {last_action && phase === 'play' && (
            <div className="text-center bg-black/20 rounded-lg px-3 sm:px-4 py-1 sm:py-1.5 text-xs sm:text-sm animate-slide-in max-w-xs">
              <span className="font-medium">{last_action.message}</span>
              {last_action.score_events.map((e, i) => (
                <span key={i} className="text-gold ml-2 font-bold">+{e.points}</span>
              ))}
            </div>
          )}
        </div>

        {/* Player zone */}
        <div className="flex flex-col gap-0.5">
          {/* Action bar (provided by caller) */}
          <div className="flex items-center justify-center gap-2 sm:gap-3 min-h-[36px] sm:min-h-[40px]">
            {actionBar}
          </div>

          {error && (
            <div className="text-red-300 text-center text-sm bg-red-900/40 rounded-lg px-3 py-1 animate-slide-in">
              {error}
              {errorExtra}
            </div>
          )}

          <CardFan
            cards={player.hand}
            selectedIndices={phase === 'discard' && yourTurn ? selectedIndices : []}
            onCardClick={onCardClick}
            disabled={loading}
          />
        </div>
      </div>

      {/* Game over modal */}
      {winner && (
        <GameOverModal
          winner={winner}
          playerName={player.name}
          opponentName={opponent.name}
          playerScore={player.score}
          opponentScore={opponent.score}
          onNewGame={onNewGame}
        />
      )}

      {extras}
    </div>
  );
}
