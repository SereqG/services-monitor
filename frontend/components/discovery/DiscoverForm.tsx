"use client";

import { useMemo } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { makeDiscoverFormSchema, type DiscoverFormValues } from "@/lib/schemas/discoverForm";
import { useI18n } from "@/lib/i18n";

export function DiscoverForm({
  onSubmit,
}: {
  onSubmit: (values: DiscoverFormValues) => void;
}) {
  const { dict } = useI18n();
  const schema = useMemo(
    () => makeDiscoverFormSchema(dict.discoverForm.validation),
    [dict],
  );
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<DiscoverFormValues>({
    resolver: zodResolver(schema),
    defaultValues: { url: "", enable_ai_summary: false },
  });

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      noValidate
      className="mt-8 flex flex-col gap-3 rounded-xl border border-border bg-card p-4 shadow-2xl"
    >
      <div className="flex w-full gap-1">
        <div className="flex flex-col gap-1 w-full">

          <input
            type="text"
            inputMode="url"
            autoComplete="url"
            placeholder={dict.discoverForm.urlPlaceholder}
            className="w-full rounded-md bg-background px-4 py-3 font-mono text-sm outline-none ring-1 ring-border placeholder:text-muted-foreground/60 focus:ring-accent aria-invalid:ring-destructive w-full"
            aria-label={dict.discoverForm.urlAriaLabel}
            aria-invalid={!!errors.url}
            {...register("url")}
          />
          {errors.url && (
            <p className="px-1 text-xs text-destructive">{errors.url.message}</p>
          )}
        </div>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-start">
          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-md bg-primary px-8 py-3 text-sm font-bold uppercase tracking-tight text-primary-foreground transition-colors hover:bg-white disabled:cursor-not-allowed disabled:opacity-50 min-w-52"
          >
            {dict.discoverForm.discoverButton}
          </button>
        </div>
      </div>


      <div className="flex gap-3">
        <div className="flex flex-1 flex-col gap-1">
          <label className="px-1 text-xs text-muted-foreground">
            {dict.discoverForm.maxPages}
          </label>
          <input
            type="number"
            inputMode="numeric"
            placeholder="500"
            min={1}
            max={500}
            className="w-full rounded-md bg-background px-4 py-2 font-mono text-sm outline-none ring-1 ring-border placeholder:text-muted-foreground/40 focus:ring-accent aria-invalid:ring-destructive"
            aria-label={dict.discoverForm.maxPagesAria}
            aria-invalid={!!errors.max_sites}
            {...register("max_sites", { setValueAs: (v) => (v === "" ? undefined : Number(v)) })}
          />
          {errors.max_sites && (
            <p className="px-1 text-xs text-destructive">{errors.max_sites.message}</p>
          )}
        </div>
        <div className="flex flex-1 flex-col gap-1">
          <label className="px-1 text-xs text-muted-foreground">
            {dict.discoverForm.maxDepth}
          </label>
          <input
            type="number"
            inputMode="numeric"
            placeholder="3"
            min={0}
            max={3}
            className="w-full rounded-md bg-background px-4 py-2 font-mono text-sm outline-none ring-1 ring-border placeholder:text-muted-foreground/40 focus:ring-accent aria-invalid:ring-destructive"
            aria-label={dict.discoverForm.maxDepthAria}
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
          <span className="text-sm font-medium">{dict.discoverForm.aiSummaryTitle}</span>
          <span className="text-xs leading-normal text-muted-foreground">
            {dict.discoverForm.aiSummaryDescription}
          </span>
        </span>
      </label>
    </form>
  );
}
