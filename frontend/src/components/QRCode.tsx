import { useEffect, useState } from "react";
import { QRCodeSVG } from "qrcode.react";

/** Clickable QR; click opens a fullscreen overlay with a large QR + the URL. Escape or click closes. */
export default function QRCode({ url }: { url: string }) {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);
  return (
    <>
      <button className="qr-btn" onClick={() => setOpen(true)} aria-label="Ampliar QR code">
        <QRCodeSVG value={url} size={240} marginSize={2} />
      </button>
      {open && (
        <div className="qr-overlay" role="dialog" aria-label="QR code da partida" onClick={() => setOpen(false)}>
          <QRCodeSVG value={url} size={Math.min(window.innerWidth, window.innerHeight) * 0.7} marginSize={2} />
          <p>{url}</p>
          <small>Clique ou pressione Esc para fechar</small>
        </div>
      )}
    </>
  );
}
