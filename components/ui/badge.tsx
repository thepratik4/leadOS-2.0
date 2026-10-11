import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-medium transition-colors select-none",
  {
    variants: {
      variant: {
        default:
          "bg-slate-900 text-white",
        secondary:
          "bg-slate-100 text-slate-700 border border-slate-200",
        outline:
          "text-slate-700 border border-slate-200 bg-white",
        destructive:
          "bg-rose-50 text-rose-700 border border-rose-200 font-semibold",
        verified:
          "bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold",
        partially_verified:
          "bg-amber-50 text-amber-800 border border-amber-200",
        unverified:
          "bg-rose-50 text-rose-700 border border-rose-200",
        unknown:
          "bg-slate-100 text-slate-600 border border-slate-200",
        high:
          "bg-emerald-50 text-emerald-800 border border-emerald-300 font-bold",
        medium:
          "bg-amber-50 text-amber-800 border border-amber-300 font-bold",
        low:
          "bg-slate-100 text-slate-600 border border-slate-300 font-medium",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
