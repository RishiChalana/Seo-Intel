import { useRef, type ReactNode } from "react";

// Inspired by the 21st.dev / Aceternity "Glowing Effect" card: a soft radial
// spotlight follows the cursor across the card surface. Kept subtle and
// on-brand (forest-green glow) to match EMIAC's restrained aesthetic.
export function GlowCard({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);

  function handleMouseMove(e: React.MouseEvent<HTMLDivElement>) {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    el.style.setProperty("--glow-x", `${e.clientX - rect.left}px`);
    el.style.setProperty("--glow-y", `${e.clientY - rect.top}px`);
  }

  return (
    <div
      ref={ref}
      onMouseMove={handleMouseMove}
      className={`group relative overflow-hidden rounded-lg border border-outline-variant bg-white shadow-module ${className}`}
    >
      <div
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background:
            "radial-gradient(240px circle at var(--glow-x, 50%) var(--glow-y, 0), rgba(0,99,68,0.10), transparent 65%)",
        }}
      />
      <div className="relative">{children}</div>
    </div>
  );
}
