import { Navigate, Route, Routes, useParams } from "react-router-dom";

// Placeholder pages; Tasks 12-16 replace each with the real screen.
function Placeholder({ title, hasId = false }: { title: string; hasId?: boolean }) {
  const { id } = useParams();
  return (
    <main style={{ padding: "var(--sp-lg)" }}>
      <h1>{title}</h1>
      {hasId && <p>Partida: {id}</p>}
    </main>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/host/login" replace />} />
      <Route path="/host/login" element={<Placeholder title="Entrar como host" />} />
      <Route path="/host/create" element={<Placeholder title="Nova partida" />} />
      <Route path="/host/lobby/:id" element={<Placeholder title="Sala de espera" hasId />} />
      <Route path="/host/match/:id" element={<Placeholder title="Partida em andamento" hasId />} />
      <Route path="/host/results/:id" element={<Placeholder title="Resultados" hasId />} />
      <Route path="/j/:id" element={<Placeholder title="Entrar na partida" hasId />} />
      <Route path="/j/:id/wait" element={<Placeholder title="Aguardando o host iniciar" hasId />} />
      <Route path="/j/:id/play" element={<Placeholder title="PUXAR!" hasId />} />
      <Route path="/j/:id/end" element={<Placeholder title="Obrigado por jogar!" hasId />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
