import { useEffect, useRef, useState } from 'react';
import { useLobbyStore } from '../../store/lobbyStore';
import { CardFan } from '../Card/CardFan';
import { CribbageBoard } from '../Board/CribbageBoard';
import { OpponentHand } from './OpponentHand';
import { StarterCard } from './StarterCard';
import { PlayArea } from './PlayArea';
import { ScoreBreakdown } from './ScoreBreakdown';
import { GameOverModal } from './GameOverModal';
import type { Card as CardType } from '../../api/types';

export function MultiplayerGameBoard() {
  const {
    gameState: game,
    error,
    sendDiscard,
    sendPlay,
    sendGo,
    sendAcknowledge,
    disconnect,
  } = useLobbyStore();

  const [selectedIndices, setSelectedIndices] = useState<number[]>([]);
  const [floatingScore, setFloatingScore] = useState<{ text: string; key: number } | null>(null);

  const [playerPlayed, setPlayerPlayed] = useState<CardType[]>([]);
  const [opponentPlayed, setOpponentPlayed] = useState<CardType[]>([]);
  const prevPileLenRef = useRef(0);

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

  useEffect(() => {
    setSelectedIndices([]);
  }, [game?.phase]);

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

  useEffect(() => {
    if (game?.phase !== 'play') {
      setPlayerPlayed([]);
      setOpponentPlayed([]);
      prevPileLenRef.current = 0;
    }
  }, [game?.phase]);

  if (!game) return null;

  const { phase, player, opponent, starter, running_total, last_action, score_breakdown, winner } = game;

  const canPlay = (i: number) => phase === 'play' && player.hand[i]?.value + running_total <= 31;
  const hasPlayableCard = phase === 'play' && player.hand.some((c) => c.value + running_total <= 31);

  const toggleSelect = (i: number) => {
    setSelectedIndices((prev) =>
      prev.includes(i) ? prev.filter((x) => x !== i) : [...prev, i]
    );
  };

  const handleDiscard = () => {
    if (selectedIndices.length === 2) {
      sendDiscard(selectedIndices);
      setSelectedIndices([]);
    }
  };

  return (
    <div className="grid grid-cols-[2fr_3fr] flex-1 min-h-0 w-full px-2 pt-1 pb-1 gap-3 relative">
      {floatingScore && (
        <div key={floatingScore.key}
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50
                     text-4xl font-bold text-gold animate-score-float pointer-events-none">
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

        <span className="text-xs opacity-40">Round {game.round_number} - MP</span>
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

          {score_breakdown && (phase === 'count_non_dealer' || phase === 'count_dealer' || phase === 'count_crib') && (
            <ScoreBreakdown breakdown={score_breakdown} label={last_action?.message || 'Score'} />
          )}

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
          <div className="flex items-center justify-center gap-3 min-h-[40px]">
            {phase === 'discard' && (
              <button onClick={handleDiscard} disabled={selectedIndices.length !== 2}
                className="bg-gold text-black font-bold py-2 px-6 rounded-xl
                           disabled:opacity-40 hover:bg-yellow-400 active:scale-95 transition-all
                           shadow-lg shadow-gold/30">
                Send to Crib
              </button>
            )}
            {phase === 'play' && !hasPlayableCard && (
              <button onClick={sendGo}
                className="bg-red-600 text-white font-bold py-2 px-6 rounded-xl
                           hover:bg-red-500 active:scale-95 transition-all animate-glow
                           shadow-lg shadow-red-600/30">
                Say Go!
              </button>
            )}
            {(phase === 'count_non_dealer' || phase === 'count_dealer' || phase === 'count_crib') && (
              <button onClick={sendAcknowledge}
                className="bg-gold text-black font-bold py-2 px-6 rounded-xl
                           hover:bg-yellow-400 active:scale-95 transition-all
                           shadow-lg shadow-gold/30">
                {phase === 'count_crib' ? 'Next Round' : 'Continue'}
              </button>
            )}
          </div>

          {error && (
            <div className="text-red-300 text-center text-sm bg-red-900/40 rounded-lg px-3 py-1">
              {error}
            </div>
          )}

          <CardFan
            cards={player.hand}
            selectedIndices={phase === 'discard' ? selectedIndices : []}
            onCardClick={(i) => {
              if (phase === 'discard') toggleSelect(i);
              else if (phase === 'play' && canPlay(i)) sendPlay(i);
            }}
          />
        </div>
      </div>

      {winner && (
        <GameOverModal
          winner={winner}
          playerName={player.name}
          playerScore={player.score}
          opponentScore={opponent.score}
          onNewGame={disconnect}
        />
      )}
    </div>
  );
}
