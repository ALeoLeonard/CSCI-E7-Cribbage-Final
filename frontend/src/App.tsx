import { useState, useEffect } from 'react';
import { useGameStore } from './store/gameStore';
import { useLobbyStore } from './store/lobbyStore';
import { Header } from './components/Layout/Header';
import { MainMenu } from './components/Layout/MainMenu';
import { GameBoard } from './components/Game/GameBoard';
import { LobbyScreen } from './components/Lobby/LobbyScreen';
import { MultiplayerGameBoard } from './components/Game/MultiplayerGameBoard';
import { StatsScreen } from './components/Stats/StatsScreen';

type Screen = 'menu' | 'single' | 'lobby' | 'multiplayer' | 'stats';

function App() {
  const [screen, setScreen] = useState<Screen>('menu');
  const [playerName, setPlayerName] = useState(
    () => localStorage.getItem('cribbage_player_name') || 'Player',
  );
  const singleGame = useGameStore((s) => s.game);
  const lobbyStatus = useLobbyStore((s) => s.status);

  const handleNameChange = (name: string) => {
    setPlayerName(name);
    localStorage.setItem('cribbage_player_name', name);
  };

  useEffect(() => {
    if (screen === 'menu' && singleGame) {
      setScreen('single');
    }
    if (screen === 'lobby' && lobbyStatus === 'in_game') {
      setScreen('multiplayer');
    }
    if (screen === 'multiplayer' && lobbyStatus === 'idle') {
      setScreen('menu');
    }
  }, [screen, singleGame, lobbyStatus]);

  const goHome = () => {
    useGameStore.setState({ game: null, selectedIndices: [], error: null });
    useLobbyStore.getState().disconnect();
    setScreen('menu');
  };

  return (
    <>
      {screen !== 'menu' && screen !== 'stats' && <Header onHome={goHome} />}
      {screen === 'single' && singleGame ? (
        <GameBoard />
      ) : screen === 'lobby' ? (
        <LobbyScreen onBack={goHome} />
      ) : screen === 'multiplayer' ? (
        <MultiplayerGameBoard />
      ) : screen === 'stats' ? (
        <StatsScreen playerName={playerName} onBack={() => setScreen('menu')} />
      ) : (
        <MainMenu
          onMultiplayer={() => setScreen('lobby')}
          onStats={() => setScreen('stats')}
          playerName={playerName}
          onNameChange={handleNameChange}
        />
      )}
    </>
  );
}

export default App;
