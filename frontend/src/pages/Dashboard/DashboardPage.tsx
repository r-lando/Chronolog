import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import {
  useActivityTimeline,
  useDifficultyDistribution,
  useLabsByCategory,
  useMitreCoverage,
  useOverview,
  useRecentActivity,
  useSkillsPracticed,
  useToolsUsed,
} from "../../hooks/useStats";
import { StatCard } from "../../components/ui/StatCard";
import { BarChartCard } from "../../components/charts/BarChartCard";
import { LineChartCard } from "../../components/charts/LineChartCard";
import { StatusBadge, DifficultyBadge, CtfStatusBadge } from "../../components/ui/Badge";
import { LoadingState, ErrorState } from "../../components/ui/StatusStates";
import { ApiError } from "../../api/client";

export function DashboardPage() {
  const { user } = useAuth();

  const { data: overview, isLoading: overviewLoading, error: overviewError } = useOverview();
  const labsByCategory = useLabsByCategory();
  const difficultyDistribution = useDifficultyDistribution();
  const activityTimeline = useActivityTimeline();
  const skillsPracticed = useSkillsPracticed();
  const toolsUsed = useToolsUsed();
  const mitreCoverage = useMitreCoverage();
  const { data: recent, isLoading: recentLoading, error: recentError } = useRecentActivity();

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-100">Welcome back, {user?.display_name}</h1>
        <p className="text-slate-500 text-sm mt-1">Your hands-on cybersecurity activity, at a glance.</p>
      </div>

      {overviewLoading && <LoadingState label="Loading dashboard..." />}
      {overviewError && (
        <ErrorState message={overviewError instanceof ApiError ? overviewError.message : "Failed to load stats."} />
      )}

      {overview && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <StatCard label="Labs completed" value={overview.labs_completed} />
            <StatCard label="CTF challenges solved" value={overview.ctf_challenges_solved} />
            <StatCard label="Learning hours" value={overview.total_learning_hours} />
            <StatCard label="Current streak" value={`${overview.current_streak_days}d`} />
            <StatCard label="Skills practiced" value={overview.skills_practiced} />
            <StatCard label="Tools used" value={overview.tools_used} />
            <StatCard label="ATT&CK techniques practiced" value={overview.techniques_practiced} />
            <StatCard label="Completed this month" value={overview.labs_completed_this_month} />
          </div>

          {overview.completed_labs_without_date > 0 && (
            <p className="text-xs text-slate-500 mb-6">
              {overview.completed_labs_without_date} completed{" "}
              {overview.completed_labs_without_date === 1 ? "lab is" : "labs are"} missing a completion date, so{" "}
              {overview.completed_labs_without_date === 1 ? "it isn't" : "they aren't"} reflected in "this month" or
              the timeline below.{" "}
              <Link to="/labs" className="text-accent-400 hover:underline">
                Add the date
              </Link>
              .
            </p>
          )}
        </>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        <LineChartCard
          title="Labs completed per month"
          data={activityTimeline.data}
          isLoading={activityTimeline.isLoading}
          error={activityTimeline.error}
        />
        <BarChartCard
          title="Difficulty distribution"
          data={difficultyDistribution.data}
          isLoading={difficultyDistribution.isLoading}
          error={difficultyDistribution.error}
        />
        <BarChartCard
          title="Labs by category"
          data={labsByCategory.data}
          isLoading={labsByCategory.isLoading}
          error={labsByCategory.error}
          horizontal
          emptyMessage="Complete or start a lab to see this breakdown."
        />
        <BarChartCard
          title="MITRE ATT&CK coverage by tactic"
          data={mitreCoverage.data}
          isLoading={mitreCoverage.isLoading}
          error={mitreCoverage.error}
          horizontal
          emptyMessage="Map a technique to a lab to see coverage here."
        />
        <BarChartCard
          title="Top skills practiced"
          data={skillsPracticed.data}
          isLoading={skillsPracticed.isLoading}
          error={skillsPracticed.error}
          horizontal
          emptyMessage="Attach a skill to a lab to see this chart."
        />
        <BarChartCard
          title="Top tools used"
          data={toolsUsed.data}
          isLoading={toolsUsed.isLoading}
          error={toolsUsed.error}
          horizontal
          emptyMessage="Attach a tool to a lab to see this chart."
        />
      </div>

      {recentLoading && <LoadingState label="Loading recent activity..." />}
      {recentError && <ErrorState message="Failed to load recent activity." />}

      {recent && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-slate-300 mb-3">Recent labs</h3>
            {recent.recent_labs.length === 0 ? (
              <p className="text-slate-500 text-sm">No labs yet.</p>
            ) : (
              <div className="space-y-2">
                {recent.recent_labs.map((lab) => (
                  <Link
                    key={lab.id}
                    to={`/labs/${lab.id}`}
                    className="flex items-center justify-between gap-2 hover:bg-surface-800 rounded px-2 py-1.5 -mx-2 transition-colors"
                  >
                    <span className="text-sm text-slate-200 truncate">{lab.title}</span>
                    <div className="flex items-center gap-1.5 shrink-0">
                      <DifficultyBadge difficulty={lab.difficulty} />
                      <StatusBadge status={lab.status} />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          <div className="card p-5">
            <h3 className="text-sm font-semibold text-slate-300 mb-3">Recent CTF challenges</h3>
            {recent.recent_ctf_challenges.length === 0 ? (
              <p className="text-slate-500 text-sm">No CTF challenges yet.</p>
            ) : (
              <div className="space-y-2">
                {recent.recent_ctf_challenges.map((challenge) => (
                  <Link
                    key={challenge.id}
                    to={`/ctfs/challenges/${challenge.id}`}
                    className="flex items-center justify-between gap-2 hover:bg-surface-800 rounded px-2 py-1.5 -mx-2 transition-colors"
                  >
                    <div className="min-w-0">
                      <p className="text-sm text-slate-200 truncate">{challenge.title}</p>
                      <p className="text-xs text-slate-500 truncate">{challenge.event_name}</p>
                    </div>
                    <CtfStatusBadge status={challenge.status} />
                  </Link>
                ))}
              </div>
            )}
          </div>

          <div className="card p-5">
            <h3 className="text-sm font-semibold text-slate-300 mb-3">Recently practiced skills</h3>
            {recent.recently_practiced_skills.length === 0 ? (
              <p className="text-slate-500 text-sm">No skills practiced yet.</p>
            ) : (
              <div className="space-y-2">
                {recent.recently_practiced_skills.map((skill) => (
                  <Link
                    key={skill.id}
                    to={`/skills/${skill.id}`}
                    className="flex items-center justify-between gap-2 hover:bg-surface-800 rounded px-2 py-1.5 -mx-2 transition-colors"
                  >
                    <span className="text-sm text-slate-200">{skill.name}</span>
                    <span className="text-xs text-slate-500">
                      {new Date(skill.last_practiced).toLocaleDateString()}
                    </span>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
