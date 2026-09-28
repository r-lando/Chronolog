import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import clsx from "clsx";

interface MarkdownEditorProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  minRows?: number;
}

/**
 * Deliberately a plain <textarea>, not a WYSIWYG/contentEditable editor.
 * The stored value is always exactly what's in the textarea — no hidden
 * editor-state-to-Markdown conversion that can drift or corrupt content.
 * "Preview" renders that same Markdown string with react-markdown so you
 * can check formatting without leaving the field.
 */
export function MarkdownEditor({ label, value, onChange, placeholder, minRows = 6 }: MarkdownEditorProps) {
  const [mode, setMode] = useState<"write" | "preview">("write");

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <label className="label mb-0">{label}</label>
        <div className="flex gap-1 text-xs">
          <button
            type="button"
            onClick={() => setMode("write")}
            className={clsx(
              "px-2 py-0.5 rounded",
              mode === "write" ? "bg-accent-500/20 text-accent-400" : "text-slate-500 hover:text-slate-300"
            )}
          >
            Write
          </button>
          <button
            type="button"
            onClick={() => setMode("preview")}
            className={clsx(
              "px-2 py-0.5 rounded",
              mode === "preview" ? "bg-accent-500/20 text-accent-400" : "text-slate-500 hover:text-slate-300"
            )}
          >
            Preview
          </button>
        </div>
      </div>

      {mode === "write" ? (
        <textarea
          className="input-field font-mono text-sm"
          style={{ minHeight: `${minRows * 1.6}rem` }}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
        />
      ) : (
        <div
          className="input-field overflow-y-auto space-y-2 text-sm leading-relaxed [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5 [&_code]:bg-surface-700 [&_code]:px-1 [&_code]:rounded [&_pre]:bg-surface-700 [&_pre]:p-3 [&_pre]:rounded [&_pre]:overflow-x-auto"
          style={{ minHeight: `${minRows * 1.6}rem` }}
        >
          {value.trim() ? (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{value}</ReactMarkdown>
          ) : (
            <p className="text-slate-500 italic">Nothing written yet.</p>
          )}
        </div>
      )}
    </div>
  );
}
