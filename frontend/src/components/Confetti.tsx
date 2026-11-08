/** Falling confetti from the P1 sheet (4x2 cells of 4px, shown at 4x); positions are deterministic, CSS does the fall.
 *  With `colors`, pieces are tinted (sheet used as a mask) in those colors. */
export function Confetti({ count = 28, colors }: { count?: number; colors?: string[] }) {
  return (
    <div className={`confetti${colors ? " tinted" : ""}`} aria-hidden="true">
      {Array.from({ length: count }, (_, i) => {
        const pos = `-${(i % 4) * 16}px -${(Math.floor(i / 4) % 2) * 16}px`;
        return (
          <i
            key={i}
            style={{
              left: `${(i * 37) % 100}%`,
              animationDelay: `${-((i * 53) % 40) / 10}s`,
              animationDuration: `${3 + ((i * 17) % 30) / 10}s`,
              backgroundPosition: pos,
              maskPosition: pos,
              ...(colors ? { backgroundColor: colors[i % colors.length] } : {}),
            }}
          />
        );
      })}
    </div>
  );
}
