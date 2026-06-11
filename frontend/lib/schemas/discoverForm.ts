import { z } from "zod";
import type { Dictionary } from "@/lib/i18n";

/**
 * Build the discover-form schema with localized validation messages.
 * Messages come from the active dictionary so errors match the chosen language.
 */
export function makeDiscoverFormSchema(v: Dictionary["discoverForm"]["validation"]) {
  return z.object({
    url: z.string().min(1, v.urlRequired).url(v.urlInvalid),
    max_sites: z
      .number()
      .int(v.intWhole)
      .min(1, v.minPages)
      .max(500, v.maxPages)
      .optional(),
    max_depth: z
      .number()
      .int(v.intWhole)
      .min(0, v.minDepth)
      .max(3, v.maxDepth)
      .optional(),
    enable_ai_summary: z.boolean(),
  });
}

export type DiscoverFormValues = z.infer<ReturnType<typeof makeDiscoverFormSchema>>;
