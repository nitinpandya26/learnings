import { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function Button({ className, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button className={cn("rounded-md bg-cyan-600 px-4 py-2 text-sm font-semibold hover:bg-cyan-500", className)} {...props} />;
}
