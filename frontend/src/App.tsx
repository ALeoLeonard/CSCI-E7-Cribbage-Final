import { useState } from 'react';
import { useGameStore } from './store/gameStore';
import { useLobbyStore } from './store/lobbyStore';
import { Header } from './components/Layout/Header';
import { MainMenu } from './components/Layout/MainMenu';
import { GameBoard } from './components/Game/GameBoard';
import { LobbyScreen } from './components/Lobby/LobbyScreen';
import { MultiplayerGameBoard } from './components/Game/MultiplayerGameBoard';

type Screen = 'menu' | 'single' | 'lobby' | 'multiplayer';

function App() {
  const [screen, setScreen] = useState<Screen>('menu');
  const singleGame = useGameStore((s) => s.game);
  const lobbyStatus = useLobbyStore((s) => s.status);

  // Auto-transition when single player game starts
  if (screen === 'menu' && singleGame) {
    setScreen('single');
  }

  // Auto-transition when multiplayer game starts
  if (screen === 'lobby' && lobbyStatus === 'in_game') {
    setScreen('multiplayer');
  }

  // When multiplayer disconnects, go back to menu
  if (screen === 'multiplayer' && lobbyStatus === 'idle') {
    setScreen('menu');
  }

  const goHome = () => {
    useGameStore.setState({ game: null, selectedIndices: [], error: null });
    useLobbyStore.getState().disconnect();
    setScreen('menu');
  };

  return (
    <>
      {screen !== 'menu' && <Header onHome={goHome} />}
      {screen === 'single' && singleGame ? (
        <GameBoard />
      ) : screen === 'lobby' ? (
        <LobbyScreen onBack={goHome} />
      ) : screen === 'multiplayer' ? (
        <MultiplayerGameBoard />
      ) : (
        <MainMenu onMultiplayer={() => setScreen('lobby')} />
      )}
    </>
  );
}

export default App;
