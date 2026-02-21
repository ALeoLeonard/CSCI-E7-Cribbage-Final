interface CribbageBoardProps {
  playerScore: number;
  opponentScore: number;
  playerName: string;
  opponentName: string;
  playerIsDealer: boolean;
}

export function CribbageBoard({
  playerScore,
  opponentScore,
  playerName,
  opponentName,
  playerIsDealer,
}: CribbageBoardProps) {
  const holes = 121;

  // S-shaped track: row 1 left→right, curve, row 2 right→left
  const generateTrack = (trackY: number) => {
    const points: { x: number; y: number }[] = [];
    const margin = 40;
    const rightEdge = 440;
    const halfHoles = Math.ceil(holes / 2);
    const curveRadius = 12;

    // Row 1: left to right (holes 0 .. halfHoles-1)
    for (let i = 0; i < halfHoles; i++) {
      const x = margin + (i / (halfHoles - 1)) * (rightEdge - margin);
      points.push({ x, y: trackY });
    }

    // Curve: semicircle from right end of row 1 to right end of row 2
    const curveSteps = 5;
    const row2Y = trackY + 24;
    for (let s = 1; s <= curveSteps; s++) {
      const angle = Math.PI * (s / (curveSteps + 1));
      const cx = rightEdge + curveRadius * Math.sin(angle);
      const cy = trackY + 12 - curveRadius * Math.cos(angle) + 12 - curveRadius;
      points.push({ x: cx, y: cy < trackY ? trackY : cy > row2Y ? row2Y : cy });
    }

    // Row 2: right to left (remaining holes)
    const remaining = holes - halfHoles + 1;
    for (let i = 0; i < remaining; i++) {
      const x = rightEdge - (i / Math.max(remaining - 1, 1)) * (rightEdge - margin);
      points.push({ x, y: row2Y });
    }

    // Trim to exactly holes+1 points (0 to 121)
    return points.slice(0, holes + 1);
  };

  const opponentTrack = generateTrack(50);
  const playerTrack = generateTrack(96);

  const clamp = (v: number) => Math.max(0, Math.min(v, holes));
  const pIdx = clamp(playerScore);
  const oIdx = clamp(opponentScore);

  // 5-hole groupings: every 5th hole gets a small gap (rendered as slightly larger)
  const isGroupBoundary = (i: number) => i > 0 && i % 5 === 0;

  return (
    <div className="w-full animate-board-glow">
      <svg viewBox="0 0 480 160" className="w-full" role="img" aria-label="Cribbage board">
        <defs>
          {/* Wood grain gradient */}
          <linearGradient id="woodGrain" x1="0" y1="0" x2="1" y2="0.3">
            <stop offset="0%" stopColor="#A0791C" />
            <stop offset="25%" stopColor="#8B6914" />
            <stop offset="50%" stopColor="#A07A1E" />
            <stop offset="75%" stopColor="#8B6914" />
            <stop offset="100%" stopColor="#9A7318" />
          </linearGradient>
          <linearGradient id="woodEdge" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#6B4F10" />
            <stop offset="100%" stopColor="#5A4210" />
          </linearGradient>
          {/* Peg glow filters */}
          <filter id="pegGlowBlue" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="pegGlowRed" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Board body */}
        <rect x="2" y="2" width="476" height="156" rx="12" fill="url(#woodEdge)" />
        <rect x="4" y="4" width="472" height="152" rx="10" fill="url(#woodGrain)" />

        {/* Subtle grain texture lines */}
        {[20, 45, 70, 95, 120, 140].map((y) => (
          <line key={y} x1="10" y1={y} x2="470" y2={y + 2} stroke="#7A6012" strokeWidth="0.5" opacity="0.3" />
        ))}

        {/* Milestone labels */}
        {[30, 60, 90].map((milestone) => {
          const idx = Math.min(milestone, opponentTrack.length - 1);
          const pt = opponentTrack[idx];
          return (
            <text key={milestone} x={pt.x} y={38} fontSize="8" fill="#FFD700" fontWeight="bold" textAnchor="middle" opacity="0.6">
              {milestone}
            </text>
          );
        })}

        {/* Opponent name + score (top) */}
        <text x="14" y="20" fontSize="10" fill="#FCA5A5" fontWeight="bold" opacity="0.9">
          {opponentName}{!playerIsDealer ? ' (D)' : ''}
        </text>
        <text x="466" y="20" fontSize="10" fill="#FCA5A5" fontWeight="bold" textAnchor="end" opacity="0.9">
          {opponentScore}
        </text>

        {/* Opponent track holes */}
        {opponentTrack.map((p, i) => (
          <circle
            key={`oh-${i}`}
            cx={p.x}
            cy={p.y}
            r={isGroupBoundary(i) ? 2.5 : 2}
            fill={i <= oIdx ? 'transparent' : '#6B4F10'}
            opacity={i <= oIdx ? 0 : 0.5}
          />
        ))}

        {/* Opponent peg */}
        {oIdx > 0 && (
          <circle
            cx={opponentTrack[oIdx].x}
            cy={opponentTrack[oIdx].y}
            r="5"
            fill="#EF4444"
            stroke="#FCA5A5"
            strokeWidth="1.5"
            filter="url(#pegGlowRed)"
            className="transition-all duration-700 ease-out"
          >
            <animate attributeName="r" values="5;6;5" dur="2s" repeatCount="indefinite" />
          </circle>
        )}

        {/* Center divider */}
        <line x1="30" y1="82" x2="450" y2="82" stroke="#6B4F10" strokeWidth="1" opacity="0.4" />

        {/* 121 finish marker */}
        <text x="24" y="88" fontSize="9" fill="#FFD700" fontWeight="bold" textAnchor="middle" opacity="0.7">121</text>

        {/* Player track holes */}
        {playerTrack.map((p, i) => (
          <circle
            key={`ph-${i}`}
            cx={p.x}
            cy={p.y}
            r={isGroupBoundary(i) ? 2.5 : 2}
            fill={i <= pIdx ? 'transparent' : '#6B4F10'}
            opacity={i <= pIdx ? 0 : 0.5}
          />
        ))}

        {/* Player peg */}
        {pIdx > 0 && (
          <circle
            cx={playerTrack[pIdx].x}
            cy={playerTrack[pIdx].y}
            r="5"
            fill="#60A5FA"
            stroke="#93C5FD"
            strokeWidth="1.5"
            filter="url(#pegGlowBlue)"
            className="transition-all duration-700 ease-out"
          >
            <animate attributeName="r" values="5;6;5" dur="2s" repeatCount="indefinite" />
          </circle>
        )}

        {/* Player name + score (bottom) */}
        <text x="14" y="142" fontSize="10" fill="#93C5FD" fontWeight="bold" opacity="0.9">
          {playerName}{playerIsDealer ? ' (D)' : ''}
        </text>
        <text x="466" y="142" fontSize="10" fill="#93C5FD" fontWeight="bold" textAnchor="end" opacity="0.9">
          {playerScore}
        </text>
      </svg>
    </div>
  );
}
