// File: frontend/src/lib/i18nInsurance.ts
//
// Helpers that map stable backend concept ids/strings to localised display
// labels. The underlying data (product_line enum values, coverage/exclusion
// concept strings) is language-independent; only the label shown to the
// user changes with the active UI language.
import type { TFunction } from "i18next";

import type { ProductLine } from "@/types/domain";

/** Bilingual {en, at} pair for a product line, e.g. for the category grid. */
export function productLinePair(
  t: TFunction,
  line: ProductLine,
): { en: string; at: string } {
  return t(`insurance:productLines.${line}`, {
    returnObjects: true,
  }) as { en: string; at: string };
}

/**
 * Single localised label for a product line — the Austrian German term when
 * the UI is in German, the English name otherwise.
 */
export function productLineLabel(
  t: TFunction,
  language: string,
  line: ProductLine,
): string {
  const pair = productLinePair(t, line);
  return language.startsWith("de") ? pair.at : pair.en;
}

/**
 * Translate a normalised coverage/exclusion/feature concept string (e.g.
 * "Theft protection") using the controlled vocabulary in insurance.json.
 * Falls back to the original English concept string if no translation is
 * registered, so unmapped catalogue data never disappears from the UI.
 */
export function translateConcept(t: TFunction, concept: string): string {
  return t(`insurance:concepts.${concept}`, { defaultValue: concept });
}
