interface CardBackProps {
  small?: boolean;
}

export function CardBack({ small }: CardBackProps) {
  return (
    <div
      className={`
        ${small ? 'w-14 h-20' : 'w-[96px] h-[134px]'}
        rounded-xl shadow-lg border-2 border-blue-800
        bg-gradient-to-br from-blue-700 via-blue-800 to-blue-900
        flex items-center justify-center
      `}
    >
      <div className={`
        ${small ? 'w-10 h-16' : 'w-[84px] h-[122px]'}
        rounded-lg border border-blue-400/30
        bg-[repeating-linear-gradient(45deg,transparent,transparent_4px,rgba(255,255,255,0.05)_4px,rgba(255,255,255,0.05)_8px)]
        flex items-center justify-center
      `}>
        <span className={`${small ? 'text-lg' : 'text-2xl'} opacity-40`}>🃏</span>
      </div>
    </div>
  );
}
