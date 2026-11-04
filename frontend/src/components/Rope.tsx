/** Rope + knot as plain CSS shapes (not club characters). */
export default function Rope({ left }: { left: number }) {
  return (
    <div className="rope">
      <div className="rope-line" />
      <div className="rope-knot" data-testid="knot" style={{ left: `${left}%` }} />
    </div>
  );
}
