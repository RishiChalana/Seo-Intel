// Inline EMIAC-style mark: a two-tone leaf (their brand is a green leaf +
// "EMIAC Technologies" wordmark). Rebuilt as SVG so there's no external asset
// dependency and it stays crisp at any size.
export function Logo({ className = "" }: { className?: string }) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <svg
        viewBox="0 0 32 32"
        className="h-7 w-7 shrink-0"
        aria-hidden="true"
        fill="none"
      >
        <path
          d="M16 3C9 6 5 12 5 20c0 4 2 7 5 9 0-8 3-14 9-19-4 6-6 12-6 20 6-2 11-7 11-15 0-6-5-10-8-12Z"
          fill="#006344"
        />
        <path
          d="M16 3C9 6 5 12 5 20c0 4 2 7 5 9 0-8 3-14 9-19Z"
          fill="#86d7b0"
        />
      </svg>
      <div className="leading-none">
        <span className="font-heading text-[17px] font-extrabold tracking-tight text-brand-deep">
          EMIAC
        </span>
        <span className="ml-1 hidden text-[9px] font-medium uppercase tracking-[0.2em] text-secondary sm:inline">
          Technologies
        </span>
      </div>
    </div>
  );
}
