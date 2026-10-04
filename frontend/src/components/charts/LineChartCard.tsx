import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ChartPoint } from "../../types/stats";
import { LoadingState, ErrorState } from "../ui/StatusStates";

const AXIS_COLOR = "#64748b";
const GRID_COLOR = "#1e2638";
const LINE_COLOR = "#5b9dd9";

function formatMonthLabel(label: string): string {
  const [year, month] = label.split("-");
  const date = new Date(Number(year), Number(month) - 1);
  return date.toLocaleDateString(undefined, { month: "short" });
}

export function LineChartCard({
  title,
  data,
  isLoading,
  error,
}: {
  title: string;
  data: ChartPoint[] | undefined;
  isLoading: boolean;
  error: unknown;
}) {
  const formatted = data?.map((point) => ({ ...point, shortLabel: formatMonthLabel(point.label) }));

  return (
    <div className="card p-5">
      <h3 className="text-sm font-semibold text-slate-300 mb-4">{title}</h3>
      {isLoading && <LoadingState label="Loading..." />}
      {Boolean(error) && <ErrorState message="Failed to load this chart." />}
      {formatted && (
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={formatted}>
            <CartesianGrid stroke={GRID_COLOR} strokeDasharray="3 3" />
            <XAxis dataKey="shortLabel" stroke={AXIS_COLOR} fontSize={12} />
            <YAxis allowDecimals={false} stroke={AXIS_COLOR} fontSize={12} />
            <Tooltip
              contentStyle={{ background: "#151b2b", border: "1px solid #1e2638", borderRadius: 6, fontSize: 12 }}
              labelStyle={{ color: "#cbd5e1" }}
              formatter={(value: number) => [`${value} labs completed`, ""]}
            />
            <Line type="monotone" dataKey="count" stroke={LINE_COLOR} strokeWidth={2} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
