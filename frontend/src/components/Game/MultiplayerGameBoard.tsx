import { useEffect, useState } from 'react';
import { useLobbyStore } from '../../store/lobbyStore';
import { BoardLayout } from './BoardLayout';
import { ChatBubble } from './ChatBubble';

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

  useEffect(() => {
    setSelectedIndices([]);
  }, [game?.phase]);

  if (!game) return null;

  const { phase, player, opponent, running_total, your_turn } = game;

  const canPlay = (i: number) => phase === 'play' && your_turn && player.hand[i]?.value + running_total <= 31;
  const hasPlayableCard = phase === 'play' && your_turn && player.hand.some((c) => c.value + running_total <= 31);

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

  const actionBar = (
    <>
      {!your_turn && phase !== 'game_over' && (
        <span className="text-xs sm:text-sm text-white/50 italic animate-pulse">
          Waiting for {opponent.name}...
        </span>
      )}
      {phase === 'discard' && your_turn && (
        <button onClick={handleDiscard} disabled={selectedIndices.length !== 2}
          className="bg-gold text-black font-bold py-1.5 sm:py-2 px-4 sm:px-6 rounded-xl text-sm sm:text-base
                     disabled:opacity-40 hover:bg-yellow-400 active:scale-95 transition-all
                     shadow-lg shadow-gold/30">
          Send to Crib
        </button>
      )}
      {phase === 'play' && your_turn && !hasPlayableCard && (
        <button onClick={sendGo}
          className="bg-red-600 text-white font-bold py-1.5 sm:py-2 px-4 sm:px-6 rounded-xl text-sm sm:text-base
                     hover:bg-red-500 active:scale-95 transition-all animate-glow
                     shadow-lg shadow-red-600/30">
          Say Go!
        </button>
      )}
      {(phase === 'count_non_dealer' || phase === 'count_dealer' || phase === 'count_crib') && (
        <button onClick={sendAcknowledge}
          className="bg-gold text-black font-bold py-1.5 sm:py-2 px-4 sm:px-6 rounded-xl text-sm sm:text-base
                     hover:bg-yellow-400 active:scale-95 transition-all
                     shadow-lg shadow-gold/30">
          {phase === 'count_crib' ? 'Next Round' : 'Continue'}
        </button>
      )}
    </>
  );

  const errorExtra = error?.includes('disconnected') ? (
    <button onClick={disconnect}
      className="ml-2 text-gold underline hover:text-yellow-400">
      Return to Menu
    </button>
  ) : undefined;

  return (
    <BoardLayout
      game={game}
      error={error}
      selectedIndices={selectedIndices}
      yourTurn={your_turn}
      actionBar={actionBar}
      errorExtra={errorExtra}
      extras={<ChatBubble />}
      onCardClick={(i) => {
        if (phase === 'discard' && your_turn) toggleSelect(i);
        else if (phase === 'play' && canPlay(i)) sendPlay(i);
      }}
      onNewGame={disconnect}
    />
  );
}
