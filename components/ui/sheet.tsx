import * as React from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface SheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
  className?: string;
}

export function Sheet({ open, onOpenChange, children, className }: SheetProps) {
  // ESC key listener
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && open) {
        onOpenChange(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onOpenChange]);

  // Lock body scroll when open
  React.useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity duration-200"
        onClick={() => onOpenChange(false)}
      />

      {/* Drawer content */}
      <div
        className={cn(
          "relative z-50 flex h-full w-full max-w-2xl flex-col bg-white shadow-2xl border-l border-slate-200 transition-transform duration-200 ease-out overflow-hidden",
          className
        )}
      >
        {children}
      </div>
    </div>
  );
}

export function SheetHeader({
  className,
  children,
  onClose,
}: {
  className?: string;
  children: React.ReactNode;
  onClose?: () => void;
}) {
  return (
    <div
      className={cn(
        "flex items-center justify-between border-b border-slate-200 px-5 py-3.5 bg-slate-50/80",
        className
      )}
    >
      <div className="flex-1 min-w-0 pr-4">{children}</div>
      {onClose && (
        <button
          onClick={onClose}
          className="rounded-md p-1.5 text-slate-400 hover:bg-slate-200/60 hover:text-slate-700 transition-colors cursor-pointer"
          title="Close panel (Esc)"
        >
          <X className="size-4" />
          <span className="sr-only">Close</span>
        </button>
      )}
    </div>
  );
}

export function SheetContent({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div className={cn("flex-1 overflow-y-auto p-5 space-y-5", className)}>
      {children}
    </div>
  );
}

export function SheetFooter({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className={cn(
        "flex items-center justify-end gap-2 border-t border-slate-200 bg-slate-50/80 px-5 py-3",
        className
      )}
    >
      {children}
    </div>
  );
}
