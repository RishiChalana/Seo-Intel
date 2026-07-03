// Official EMIAC Technologies logo. Served from frontend/public.
export function Logo({ className = "" }: { className?: string }) {
  return (
    <img
      src="/emiac-logo.png"
      alt="EMIAC Technologies"
      className={`h-9 w-auto object-contain ${className}`}
    />
  );
}
