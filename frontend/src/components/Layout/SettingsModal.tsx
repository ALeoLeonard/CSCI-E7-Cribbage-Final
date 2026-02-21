import { useSoundStore } from '../../store/soundStore';

interface SettingsModalProps {
  onClose: () => void;
}

export function SettingsModal({ onClose }: SettingsModalProps) {
  const { enabled, toggle } = useSoundStore();

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 backdrop-blur-sm p-4">
      <div className="bg-felt-dark rounded-2xl p-6 max-w-sm w-full border border-white/10 shadow-2xl">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Settings</h2>
          <button
            onClick={onClose}
            className="text-white/60 hover:text-white text-2xl leading-none"
            aria-label="Close settings"
          >
            &times;
          </button>
        </div>

        <div className="space-y-4">
          {/* Sound toggle */}
          <div className="flex items-center justify-between bg-black/20 rounded-xl p-4">
            <div>
              <div className="font-medium">Sound Effects</div>
              <div className="text-xs opacity-60">Card sounds & score alerts</div>
            </div>
            <button
              onClick={toggle}
              className={`w-14 h-8 rounded-full transition-colors relative ${
                enabled ? 'bg-gold' : 'bg-white/20'
              }`}
              role="switch"
              aria-checked={enabled}
              aria-label="Toggle sound effects"
            >
              <div
                className={`absolute top-1 w-6 h-6 rounded-full bg-white shadow transition-transform ${
                  enabled ? 'translate-x-7' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* How to Play */}
          <div className="bg-black/20 rounded-xl p-4">
            <h3 className="font-medium mb-2">How to Play</h3>
            <div className="text-xs opacity-70 space-y-1">
              <p><strong>Goal:</strong> Be the first to reach 121 points.</p>
              <p><strong>Deal:</strong> 6 cards each. Discard 2 to the crib.</p>
              <p><strong>Play:</strong> Take turns playing cards. Total can't exceed 31.</p>
              <p><strong>Scoring:</strong> 15s (2pts), pairs (2pts), runs (1pt/card), flush (4-5pts), nobs (1pt).</p>
              <p><strong>Pegging:</strong> 15=2pts, 31=2pts, pairs, runs, last card=1pt.</p>
              <p><strong>Count order:</strong> Non-dealer, dealer hand, then dealer's crib.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
