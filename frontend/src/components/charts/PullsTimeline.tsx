import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { AnalyticsPayload } from "../../types/api";
import { fonts, teams } from "../../theme/tokens";

const tick = { fontFamily: fonts.pixel, fontSize: 10, fill: "#9a9ab0" };

export default function PullsTimeline({ data }: { data: AnalyticsPayload["pullsPerSecond"] }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data}>
        <CartesianGrid stroke="#2c3778" strokeDasharray="4 4" />
        <XAxis dataKey="t" unit="s" stroke="#4a58a0" tick={tick} />
        <YAxis stroke="#4a58a0" tick={tick} />
        <Tooltip
          contentStyle={{ background: "#0a0c22", border: "4px solid #2c3778", borderRadius: 0, fontFamily: fonts.pixel, fontSize: 10 }}
          cursor={{ stroke: "#ffe27a" }}
        />
        <Legend wrapperStyle={{ fontFamily: fonts.pixel, fontSize: 10 }} />
        <Line type="stepAfter" dataKey="inter" name="Inter" stroke={teams.inter.primary} strokeWidth={4} dot={false} isAnimationActive={false} />
        <Line type="stepAfter" dataKey="gremio" name="Grêmio" stroke={teams.gremio.light} strokeWidth={4} dot={false} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
