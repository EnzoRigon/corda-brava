import HostCreate from "./pages/HostCreate";
import HostLobby from "./pages/HostLobby";
import HostLogin from "./pages/HostLogin";
import HostMatch from "./pages/HostMatch";
import HostResults from "./pages/HostResults";
import PlayerEnd from "./pages/PlayerEnd";
import PlayerJoin from "./pages/PlayerJoin";
import PlayerPlay from "./pages/PlayerPlay";
import PlayerWait from "./pages/PlayerWait";
import { Navigate, Route, Routes } from "react-router-dom";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/host/login" replace />} />
      <Route path="/host/login" element={<HostLogin />} />
      <Route path="/host/create" element={<HostCreate />} />
      <Route path="/host/lobby/:id" element={<HostLobby />} />
      <Route path="/host/match/:id" element={<HostMatch />} />
      <Route path="/host/results/:id" element={<HostResults />} />
      <Route path="/j/:id" element={<PlayerJoin />} />
      <Route path="/j/:id/wait" element={<PlayerWait />} />
      <Route path="/j/:id/play" element={<PlayerPlay />} />
      <Route path="/j/:id/end" element={<PlayerEnd />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
