import { useState } from "react";
import { Clock, FileUp, Plus, Share2, Users } from "lucide-react";
import { ScoreBento } from "./ScoreBento";
import { OutlineDocument } from "./OutlineDocument";
import { TelemetryCard } from "./TelemetryCard";
import { KeywordClusters } from "./KeywordClusters";
import { ContentGaps } from "./ContentGaps";
import { ExportModal } from "./ExportModal";
import type { ContentBrief } from "../lib/types";

export function Dashboard({
  brief,
  onNewBrief,
}: {
  brief: ContentBrief;
  onNewBrief: () => void;
}) {
  const [exportOpen, setExportOpen] = useState(false);

  return (
    <div className="mx-auto max-w-container px-4 py-6 md:px-margin-desktop">
      {/* Sticky sub-header: topic + actions */}
      <div className="no-print sticky top-16 z-30 mb-gutter flex flex-col gap-4 border-b border-outline-variant bg-surface-paper/95 py-4 backdrop-blur-sm sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="mb-1 flex items-center gap-2">
            <span className="rounded-sm border border-surface-tint/20 bg-surface-tint/10 px-2 py-0.5 text-[11px] font-medium uppercase tracking-widest text-surface-tint">
              Content Brief
            </span>
            <span className="flex items-center gap-1 text-[11px] text-secondary">
              <Clock size={12} /> Generated just now
            </span>
            <span className="flex items-center gap-1 text-[11px] text-secondary">
              <Users size={12} /> {brief.competitor_pages_analyzed} competitors
              analyzed
            </span>
          </div>
          <h1 className="font-heading text-2xl font-semibold capitalize text-on-surface md:text-3xl">
            {brief.topic}
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onNewBrief}
            className="flex items-center gap-2 rounded border border-outline-variant px-4 py-2 text-sm font-medium text-secondary transition-colors hover:border-primary hover:text-primary"
          >
            <Plus size={16} /> New
          </button>
          <button className="flex items-center gap-2 rounded border border-primary px-4 py-2 text-sm font-medium text-primary transition-colors hover:bg-primary/5">
            <Share2 size={16} /> Share
          </button>
          <button
            onClick={() => setExportOpen(true)}
            className="flex items-center gap-2 rounded bg-primary-container px-5 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-brand-deep"
          >
            <FileUp size={16} /> Export Brief
          </button>
        </div>
      </div>

      {/* Two-column grid */}
      <div className="grid grid-cols-1 gap-gutter xl:grid-cols-12">
        <div className="space-y-gutter xl:col-span-8">
          <ScoreBento score={brief.score} />
          <OutlineDocument outline={brief.outline} />
        </div>
        <div className="space-y-gutter xl:col-span-4">
          <TelemetryCard usage={brief.usage} />
          <KeywordClusters clusters={brief.keyword_clusters} />
          <ContentGaps gaps={brief.outline.content_gaps_addressed} />
        </div>
      </div>

      {exportOpen && (
        <ExportModal brief={brief} onClose={() => setExportOpen(false)} />
      )}
    </div>
  );
}
