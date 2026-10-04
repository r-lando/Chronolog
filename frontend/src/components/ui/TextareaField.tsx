import type { TextareaHTMLAttributes } from "react";

interface TextareaFieldProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  hint?: string;
}

export function TextareaField({ label, hint, id, ...props }: TextareaFieldProps) {
  return (
    <div>
      <label className="label" htmlFor={id}>
        {label}
      </label>
      <textarea id={id} className="input-field font-mono text-sm min-h-[100px]" {...props} />
      {hint && <p className="text-xs text-slate-500 mt-1">{hint}</p>}
    </div>
  );
}
