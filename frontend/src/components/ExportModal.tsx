import { useState } from "react";
import { motion } from "framer-motion";
import { Braces, Download, FileText, Hash, X } from "lucide-react";
import type { ContentBrief } from "../lib/types";
import { downloadJson, downloadMarkdown, downloadPdf } from "../lib/export";

type Format = "pdf" | "markdown" | "json";

const OPTIONS: {
  id: Format;
  icon: typeof FileText;
  title: string;
  desc: string;
}[] = [
  {
    id: "pdf",
    icon: FileText,
    title: "PDF Document",
    desc: "Formatted, print-ready outline. Best for sharing with clients.",
  },
  {
    id: "markdown",
    icon: Hash,
    title: "Markdown (.md)",
    desc: "Clean text format. Ideal for Notion, Obsidian, or a CMS.",
  },
  {
    id: "json",
    icon: Braces,
    title: "Raw Data (JSON)",
    desc: "Full structured payload. Best for programmatic ingestion.",
  },
];

export function ExportModal({
  brief,
  onClose,
}: {
  brief: ContentBrief;
  onClose: () => void;
}) {
  const [selected, setSelected] = useState<Format>("pdf");

  function handleDownload() {
    if (selected === "markdown") downloadMarkdown(brief);
    else if (selected === "json") downloadJson(brief);
    else downloadPdf();
    if (selected !== "pdf") onClose();
  }

  return (
    <div className="no-print fixed inset-0 z-[60] flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-on-surface/40 backdrop-blur-sm"
        onClick={onClose}
      />
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 8 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        className="relative flex w-full max-w-2xl flex-col overflow-hidden rounded-xl bg-white shadow-modal md:flex-row"
      >
        {/* Preview panel */}
        <div className="hidden w-2/5 flex-col items-center justify-center border-r border-surface-variant bg-surface-paper p-6 md:flex">
          <div className="w-full max-w-[180px] rounded-lg border border-outline-variant bg-white p-4 shadow-sm">
            <div className="mb-2 h-2 w-3/4 rounded-full bg-surface-container" />
            <div className="mb-4 h-1.5 w-1/2 rounded-full bg-surface-container-high" />
            <div className="flex h-16 items-end gap-1.5">
              {[40, 70, 55, 90].map((h, i) => (
                <div
                  key={i}
                  className="flex-1 rounded-sm bg-primary-fixed-dim"
                  style={{ height: `${h}%` }}
                />
              ))}
            </div>
          </div>
          <p className="mt-4 text-center text-sm font-medium text-on-surface">
            {brief.topic}
          </p>
          <p className="text-center text-xs text-secondary">
            {brief.outline.sections.length} sections ·{" "}
            {brief.outline.estimated_word_count.toLocaleString()} words
          </p>
        </div>

        {/* Options panel */}
        <div className="flex-1 p-6">
          <div className="mb-5 flex items-start justify-between">
            <div>
              <h2 className="font-heading text-xl font-bold text-on-surface">
                Export Intelligence
              </h2>
              <p className="text-sm text-secondary">
                Select your preferred format for the final deliverable.
              </p>
            </div>
            <button
              onClick={onClose}
              className="rounded-full p-1 text-secondary hover:bg-surface-container-low"
            >
              <X size={20} />
            </button>
          </div>

          <div className="space-y-3">
            {OPTIONS.map((opt) => {
              const Icon = opt.icon;
              const active = selected === opt.id;
              return (
                <button
                  key={opt.id}
                  onClick={() => setSelected(opt.id)}
                  className={`flex w-full items-center gap-3 rounded-lg border p-3 text-left transition-all ${
                    active
                      ? "border-primary bg-primary-fixed/15 ring-1 ring-primary"
                      : "border-outline-variant hover:border-outline"
                  }`}
                >
                  <div
                    className={`flex h-9 w-9 shrink-0 items-center justify-center rounded ${
                      active
                        ? "bg-primary-container text-white"
                        : "bg-surface-container text-secondary"
                    }`}
                  >
                    <Icon size={18} />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-on-surface">
                      {opt.title}
                    </p>
                    <p className="text-xs text-secondary">{opt.desc}</p>
                  </div>
                  <div
                    className={`h-4 w-4 rounded-full border-2 ${
                      active
                        ? "border-primary bg-primary"
                        : "border-outline-variant"
                    }`}
                  />
                </button>
              );
            })}
          </div>

          <div className="mt-6 flex items-center justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-secondary hover:text-on-surface"
            >
              Cancel
            </button>
            <button
              onClick={handleDownload}
              className="flex items-center gap-2 rounded bg-primary px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-deep"
            >
              <Download size={16} /> Download
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
