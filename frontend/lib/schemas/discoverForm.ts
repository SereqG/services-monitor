import { z } from "zod";

export const discoverFormSchema = z.object({
  url: z
    .string()
    .min(1, "URL is required")
    .url("Must be a valid URL (e.g. https://example.com)"),
  max_sites: z
    .number()
    .int("Must be a whole number")
    .min(1, "Must be at least 1")
    .max(500, "Cannot exceed 500")
    .optional(),
  max_depth: z
    .number()
    .int("Must be a whole number")
    .min(0, "Must be 0 or greater")
    .max(3, "Cannot exceed 3")
    .optional(),
  enable_ai_summary: z.boolean(),
});

export type DiscoverFormValues = z.infer<typeof discoverFormSchema>;
