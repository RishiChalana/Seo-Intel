import { Plus } from "lucide-react";
import { Logo } from "./Logo";

interface HeaderProps {
  showNav: boolean;
  topic?: string;
  onNewBrief: () => void;
}

export function Header({ showNav, onNewBrief }: HeaderProps) {
  return (
    <header className="sticky top-0 z-50 flex h-16 items-center justify-between border-b border-surface-variant bg-white px-6 md:px-margin-desktop">
      <div className="flex items-center gap-8">
        <button onClick={onNewBrief} className="flex items-center" aria-label="Home">
          <Logo />
        </button>
        {showNav && (
          <nav className="hidden items-center gap-6 md:flex">
            {["Projects", "Briefs", "Workflows", "Analytics"].map((item) => (
              <a
                key={item}
                href="#"
                className={
                  item === "Briefs"
                    ? "border-b-2 border-primary pb-1 text-sm font-bold text-primary"
                    : "text-sm text-secondary transition-colors hover:text-primary"
                }
              >
                {item}
              </a>
            ))}
          </nav>
        )}
      </div>

      {showNav && (
        <button
          onClick={onNewBrief}
          className="hidden items-center gap-1.5 rounded bg-primary-container px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-brand-deep sm:flex"
        >
          <Plus size={16} /> New Brief
        </button>
      )}
    </header>
  );
}
