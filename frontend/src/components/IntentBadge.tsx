import type { SearchIntent } from "../lib/types";

const STYLES: Record<SearchIntent, string> = {
  commercial: "bg-primary-container/10 text-primary-container",
  informational: "bg-secondary/10 text-secondary",
  transactional: "bg-amber/10 text-amber",
  navigational: "bg-outline/10 text-outline",
};

export function IntentBadge({ intent }: { intent: SearchIntent }) {
  return (
    <span
      className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${STYLES[intent]}`}
    >
      {intent}
    </span>
  );
}
