/** Falling confetti from the P1 sheet (4x2 cells of 4px, shown at 4x); positions are deterministic, CSS does the fall. */
export function Confetti({ count = 28 }: { count?: number }) {
  return (
    <div className="confetti" aria-hidden="true">
      {Array.from({ length: count }, (_, i) => (
        <i
          key={i}
          style={{
            left: `${(i * 37) % 100}%`,
            animationDelay: `${-((i * 53) % 40) / 10}s`,
            animationDuration: `${3 + ((i * 17) % 30) / 10}s`,
            backgroundPosition: `-${(i % 4) * 16}px -${(Math.floor(i / 4) % 2) * 16}px`,
          }}
        />
      ))}
    </div>
  );
}
