import { Area, AreaChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { AnalyticsPayload } from "../../types/api";
import { teams } from "../../theme/tokens";

export default function PullsTimeline({ data }: { data: AnalyticsPayload["pullsPerSecond"] }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={data}>
        <CartesianGrid stroke="#333" />
        <XAxis dataKey="t" unit="s" stroke="#9a9ab0" />
        <YAxis stroke="#9a9ab0" />
        <Tooltip contentStyle={{ background: "#1d1d2e" }} />
        <Legend />
        <Area type="monotone" dataKey="inter" name="Inter" stroke={teams.inter.primary} fill={teams.inter.primary} fillOpacity={0.4} />
        <Area type="monotone" dataKey="gremio" name="Grêmio" stroke={teams.gremio.primary} fill={teams.gremio.primary} fillOpacity={0.4} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
