import { useState } from 'react';
import { SettingsModal } from './SettingsModal';

interface HeaderProps {
  onHome?: () => void;
}

export function Header({ onHome }: HeaderProps) {
  const [showSettings, setShowSettings] = useState(false);

  return (
    <>
      <header className="flex items-center justify-between px-4 py-2 bg-black/20 backdrop-blur-sm">
        {onHome ? (
          <button
            onClick={onHome}
            className="text-sm opacity-70 hover:opacity-100 transition-opacity"
            aria-label="Return to main menu"
          >
            &larr; Menu
          </button>
        ) : (
          <div />
        )}
        <span className="font-bold text-lg">Cribbage</span>
        <button
          onClick={() => setShowSettings(true)}
          className="text-xl opacity-70 hover:opacity-100 transition-opacity"
          aria-label="Open settings"
        >
          &#9881;
        </button>
      </header>
      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
    </>
  );
}
