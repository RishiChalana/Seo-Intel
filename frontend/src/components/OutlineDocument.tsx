import { FileText } from "lucide-react";
import type { ContentOutline } from "../lib/types";

const LEVEL_STYLES: Record<
  number,
  { tag: string; heading: string; border: string; margin: string }
> = {
  1: {
    tag: "text-surface-tint border-surface-tint/40",
    heading: "font-heading text-2xl md:text-3xl text-on-surface leading-tight",
    border: "border-surface-tint/30",
    margin: "",
  },
  2: {
    tag: "text-secondary border-outline-variant",
    heading: "font-heading text-xl text-on-surface",
    border: "border-outline-variant",
    margin: "ml-4",
  },
  3: {
    tag: "text-secondary border-surface-variant",
    heading: "font-heading text-lg text-on-surface-variant",
    border: "border-surface-variant",
    margin: "ml-10",
  },
};

export function OutlineDocument({ outline }: { outline: ContentOutline }) {
  return (
    <div
      id="print-area"
      className="rounded-lg border border-outline-variant bg-white p-6 shadow-module md:p-8"
    >
      <div className="mb-6 flex items-center justify-between border-b border-surface-variant pb-4">
        <h2 className="flex items-center gap-2 font-heading text-xl font-semibold text-on-surface">
          <FileText size={20} className="text-surface-tint" /> Suggested Outline
        </h2>
        <span className="rounded bg-surface px-2 py-1 text-xs text-secondary">
          Target: {outline.estimated_word_count.toLocaleString()} words
        </span>
      </div>

      {/* Title + meta */}
      <div className="mb-8 rounded-lg bg-surface-bright p-4">
        <p className="mb-1 text-[11px] font-medium uppercase tracking-wider text-secondary">
          Working Title
        </p>
        <h1 className="font-heading text-2xl font-bold leading-tight text-brand-deep">
          {outline.title}
        </h1>
        <p className="mt-2 text-sm italic text-secondary">
          {outline.meta_description}
        </p>
      </div>

      <div className="max-w-3xl space-y-5">
        {outline.sections.map((section, i) => {
          const style = LEVEL_STYLES[section.level] ?? LEVEL_STYLES[2];
          return (
            <div
              key={i}
              className={`relative border-l-2 pb-2 pl-6 ${style.border} ${style.margin}`}
            >
              <div
                className={`absolute -left-3 top-1 rounded-full border bg-white px-1 py-0.5 text-[10px] font-bold ${style.tag}`}
              >
                H{section.level}
              </div>
              <h3 className={`mb-2 ${style.heading}`}>{section.heading}</h3>

              {section.talking_points.length > 0 && (
                <ul className="mb-2 list-disc space-y-1 pl-5 text-sm text-secondary">
                  {section.talking_points.map((tp, j) => (
                    <li key={j}>{tp}</li>
                  ))}
                </ul>
              )}

              {section.target_keywords.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {section.target_keywords.map((kw) => (
                    <span
                      key={kw}
                      className="rounded-sm bg-surface px-2 py-0.5 text-[10px] text-secondary"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
