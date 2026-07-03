import { Network } from "lucide-react";
import { IntentBadge } from "./IntentBadge";
import type { KeywordCluster } from "../lib/types";

export function KeywordClusters({
  clusters,
}: {
  clusters: KeywordCluster[];
}) {
  return (
    <div className="rounded-lg border border-outline-variant bg-white p-6 shadow-module">
      <h3 className="mb-4 flex items-center gap-2 font-heading text-xl font-semibold text-on-surface">
        <Network size={20} className="text-surface-tint" /> Semantic Clusters
      </h3>
      <div className="space-y-4">
        {clusters.map((cluster) => (
          <div
            key={cluster.primary_keyword}
            className="rounded border border-surface-variant bg-surface-bright p-3"
          >
            <div className="mb-2 flex items-start justify-between gap-2">
              <span className="font-heading text-sm font-bold text-on-surface">
                {cluster.primary_keyword}
              </span>
              <IntentBadge intent={cluster.intent} />
            </div>
            <div className="flex flex-wrap gap-1.5">
              {cluster.related_keywords.slice(0, 8).map((kw) => (
                <span
                  key={kw}
                  className="rounded border border-outline-variant bg-white px-2 py-1 text-[11px] text-on-surface-variant"
                >
                  {kw}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
