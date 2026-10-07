import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ChartPoint } from "../../types/stats";
import { LoadingState, ErrorState } from "../ui/StatusStates";

const AXIS_COLOR = "#64748b"; // slate-500-ish, readable on dark background
const GRID_COLOR = "#1e2638"; // surface-700
const BAR_COLOR = "#3d7ebf"; // accent-500

export function BarChartCard({
  title,
  data,
  isLoading,
  error,
  horizontal = false,
  emptyMessage = "No data yet.",
}: {
  title: string;
  data: ChartPoint[] | undefined;
  isLoading: boolean;
  error: unknown;
  horizontal?: boolean;
  emptyMessage?: string;
}) {
  return (
    <div className="card p-5">
      <h3 className="text-sm font-semibold text-slate-300 mb-4">{title}</h3>
      {isLoading && <LoadingState label="Loading..." />}
      {Boolean(error) && <ErrorState message="Failed to load this chart." />}
      {data && data.length === 0 && <p className="text-slate-500 text-sm py-8 text-center">{emptyMessage}</p>}
      {data && data.length > 0 && (
        <ResponsiveContainer width="100%" height={horizontal ? Math.max(160, data.length * 32) : 220}>
          <BarChart data={data} layout={horizontal ? "vertical" : "horizontal"} margin={{ left: horizontal ? 60 : 0 }}>
            <CartesianGrid stroke={GRID_COLOR} strokeDasharray="3 3" />
            {horizontal ? (
              <>
                <XAxis type="number" allowDecimals={false} stroke={AXIS_COLOR} fontSize={12} />
                <YAxis type="category" dataKey="label" stroke={AXIS_COLOR} fontSize={12} width={100} />
              </>
            ) : (
              <>
                <XAxis dataKey="label" stroke={AXIS_COLOR} fontSize={12} />
                <YAxis allowDecimals={false} stroke={AXIS_COLOR} fontSize={12} />
              </>
            )}
            <Tooltip
              contentStyle={{ background: "#151b2b", border: "1px solid #1e2638", borderRadius: 6, fontSize: 12 }}
              labelStyle={{ color: "#cbd5e1" }}
              cursor={{ fill: "rgba(255,255,255,0.03)" }}
            />
            <Bar dataKey="count" fill={BAR_COLOR} radius={horizontal ? [0, 3, 3, 0] : [3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
