/**
 * Fill `{name}` placeholders in a template from a params object. Missing keys are
 * left as the literal `{name}` so gaps are visible rather than silently blank.
 */
export function interpolate(
  template: string,
  params: Record<string, string | number> = {},
): string {
  return template.replace(/\{(\w+)\}/g, (match, key: string) =>
    key in params ? String(params[key]) : match,
  );
}
