import { Link, useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { usePublicLab } from "../../hooks/usePortfolio";
import { getPublicEvidenceFileUrl } from "../../api/portfolio";
import { DifficultyBadge } from "../../components/ui/Badge";
import { LoadingState } from "../../components/ui/StatusStates";

function Section({ title, content }: { title: string; content: string | null }) {
  if (!content) return null;
  return (
    <section className="mb-8">
      <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide mb-2">{title}</h2>
      <div className="text-sm text-slate-300 leading-relaxed space-y-2 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
      </div>
    </section>
  );
}

export function PublicLabPage() {
  const { slug } = useParams<{ slug: string }>();
  const { data: lab, isLoading, error } = usePublicLab(slug);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-surface-950">
        <LoadingState label="Loading..." />
      </div>
    );
  }

  if (error || !lab) {
    return (
      <div className="min-h-screen bg-surface-950 flex items-center justify-center px-6">
        <div className="text-center">
          <h1 className="text-xl font-semibold text-slate-200">This lab isn't published</h1>
          <p className="text-slate-500 text-sm mt-2">
            It may have been unpublished, or the link may be incorrect.
          </p>
          <Link to="/p" className="text-accent-400 hover:underline text-sm mt-4 inline-block">
            ← Back to portfolio
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-950">
      <div className="max-w-3xl mx-auto px-6 py-12">
        <Link to="/p" className="text-xs text-slate-500 hover:text-accent-400">
          ← Back to portfolio
        </Link>

        <header className="mt-2 mb-8">
          <div className="flex items-center gap-2 mb-2">
            <DifficultyBadge difficulty={lab.difficulty} />
            <span className="text-sm text-slate-500">{lab.category}</span>
            {lab.platform && <span className="text-sm text-slate-500">· {lab.platform}</span>}
          </div>
          <h1 className="text-2xl font-bold text-slate-100">{lab.title}</h1>
          {lab.summary && <p className="text-slate-400 mt-2">{lab.summary}</p>}
        </header>

        {(lab.skills.length > 0 || lab.tools.length > 0) && (
          <div className="flex flex-wrap gap-2 mb-8">
            {lab.skills.map((skill) => (
              <span key={skill} className="text-xs bg-surface-800 border border-surface-700 text-slate-300 px-2 py-1 rounded">
                {skill}
              </span>
            ))}
            {lab.tools.map((tool) => (
              <span key={tool} className="text-xs bg-surface-800 border border-accent-500/30 text-accent-400 px-2 py-1 rounded">
                {tool}
              </span>
            ))}
          </div>
        )}

        <Section title="Objective" content={lab.objective} />
        <Section title="Environment" content={lab.environment} />
        <Section title="Methodology" content={lab.methodology} />
        <Section title="Findings" content={lab.findings} />

        {lab.evidence.length > 0 && (
          <section className="mb-8">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide mb-2">Evidence</h2>
            <div className="space-y-2">
              {lab.evidence.map((item) => (
                <a
                  key={item.id}
                  href={getPublicEvidenceFileUrl(item.id)}
                  target="_blank"
                  rel="noreferrer"
                  className="block bg-surface-800 border border-surface-700 rounded-md px-4 py-2 hover:border-accent-500/50 transition-colors"
                >
                  <span className="text-sm text-accent-400">{item.original_filename}</span>
                  {item.description && <p className="text-xs text-slate-500 mt-0.5">{item.description}</p>}
                </a>
              ))}
            </div>
          </section>
        )}

        <Section title="Analysis" content={lab.analysis} />

        {lab.techniques.length > 0 && (
          <section className="mb-8">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide mb-2">
              MITRE ATT&CK Techniques
            </h2>
            <div className="space-y-2">
              {lab.techniques.map((technique) => (
                <div key={technique.technique_id} className="bg-surface-800 border border-surface-700 rounded-md px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-slate-500">
                      {technique.sub_technique_id ?? technique.technique_id}
                    </span>
                    <span className="text-sm font-medium text-slate-200">{technique.name}</span>
                    <span className="text-xs bg-surface-700 text-slate-400 px-1.5 py-0.5 rounded">
                      {technique.tactic}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1.5">{technique.justification}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        <Section title="Lessons Learned" content={lab.lessons_learned} />
        <Section title="Next Steps" content={lab.next_steps} />

        <footer className="mt-12 pt-6 border-t border-surface-700 text-xs text-slate-600">
          Published {new Date(lab.published_at).toLocaleDateString()} · Built with TALA
        </footer>
      </div>
    </div>
  );
}
