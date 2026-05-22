"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { discoverFormSchema, type DiscoverFormValues } from "@/lib/schemas/discoverForm";

export function DiscoverForm({
  onSubmit,
}: {
  onSubmit: (values: DiscoverFormValues) => void;
}) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<DiscoverFormValues>({
    resolver: zodResolver(discoverFormSchema),
    defaultValues: { url: "", email: "", enable_ai_summary: false },
  });

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      noValidate
      className="mt-8 flex flex-col gap-3 rounded-xl border border-border bg-card p-4 shadow-2xl"
    >
      <div className="flex flex-col gap-1">
        <input
          type="text"
          inputMode="url"
          autoComplete="url"
          placeholder="https://example.com"
          className="w-full rounded-md bg-background px-4 py-3 font-mono text-sm outline-none ring-1 ring-border placeholder:text-muted-foreground/60 focus:ring-accent aria-invalid:ring-destructive"
          aria-label="Website URL"
          aria-invalid={!!errors.url}
          {...register("url")}
        />
        {errors.url && (
          <p className="px-1 text-xs text-destructive">{errors.url.message}</p>
        )}
      </div>

      <div className="flex flex-col gap-2 sm:flex-row sm:items-start">
        <div className="flex flex-1 flex-col gap-1">
          <input
            type="email"
            autoComplete="email"
            placeholder="your@email.com"
            className="w-full rounded-md bg-background px-4 py-3 font-mono text-sm outline-none ring-1 ring-border placeholder:text-muted-foreground/60 focus:ring-accent aria-invalid:ring-destructive"
            aria-label="Email address"
            aria-invalid={!!errors.email}
            {...register("email")}
          />
          {errors.email && (
            <p className="px-1 text-xs text-destructive">{errors.email.message}</p>
          )}
        </div>
        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-md bg-primary px-8 py-3 text-sm font-bold uppercase tracking-tight text-primary-foreground transition-colors hover:bg-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          Discover pages
        </button>
      </div>

      <div className="flex gap-3">
        <div className="flex flex-1 flex-col gap-1">
          <label className="px-1 text-xs text-muted-foreground">
            Max pages
          </label>
          <input
            type="number"
            inputMode="numeric"
            placeholder="500"
            min={1}
            max={500}
            className="w-full rounded-md bg-background px-4 py-2 font-mono text-sm outline-none ring-1 ring-border placeholder:text-muted-foreground/40 focus:ring-accent aria-invalid:ring-destructive"
            aria-label="Max pages to discover"
            aria-invalid={!!errors.max_sites}
            {...register("max_sites", { setValueAs: (v) => (v === "" ? undefined : Number(v)) })}
          />
          {errors.max_sites && (
            <p className="px-1 text-xs text-destructive">{errors.max_sites.message}</p>
          )}
        </div>
        <div className="flex flex-1 flex-col gap-1">
          <label className="px-1 text-xs text-muted-foreground">
            Max depth
          </label>
          <input
            type="number"
            inputMode="numeric"
            placeholder="3"
            min={0}
            max={3}
            className="w-full rounded-md bg-background px-4 py-2 font-mono text-sm outline-none ring-1 ring-border placeholder:text-muted-foreground/40 focus:ring-accent aria-invalid:ring-destructive"
            aria-label="Max crawl depth"
            aria-invalid={!!errors.max_depth}
            {...register("max_depth", { setValueAs: (v) => (v === "" ? undefined : Number(v)) })}
          />
          {errors.max_depth && (
            <p className="px-1 text-xs text-destructive">{errors.max_depth.message}</p>
          )}
        </div>
      </div>

      <label className="flex cursor-pointer items-start gap-3 rounded-md bg-background px-4 py-3 ring-1 ring-border">
        <input
          type="checkbox"
          className="mt-0.5 size-4 accent-accent"
          {...register("enable_ai_summary")}
        />
        <span className="flex flex-col gap-0.5">
          <span className="text-sm font-medium">AI-Powered Summary</span>
          <span className="text-xs leading-normal text-muted-foreground">
            Get a simplified explanation of your audit results, including overall
            website health, key problems, and recommended improvements. AI summaries
            take slightly longer to generate and may increase processing cost.
          </span>
        </span>
      </label>
    </form>
  );
}
