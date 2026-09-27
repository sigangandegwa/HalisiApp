import { en, type MessageKey } from "./en";
import { sw } from "./sw";

export type Locale = "en" | "sw";
export type Messages = Record<MessageKey, string>;
export type { MessageKey };
export type Vars = Record<string, string | number>;

export const LOCALE_COOKIE = "halisi_locale";
export const LOCALES: readonly Locale[] = ["en", "sw"];

export const dictionaries: Record<Locale, Messages> = { en, sw };

export function isLocale(value: unknown): value is Locale {
  return value === "en" || value === "sw";
}

export function defaultLocale(): Locale {
  const env = process.env.NEXT_PUBLIC_DEFAULT_LOCALE;
  return isLocale(env) ? env : "en";
}

/** Fill `{name}` placeholders. Missing variables are left visible so they get noticed. */
export function format(template: string, vars?: Vars): string {
  if (!vars) return template;
  return template.replace(/\{(\w+)\}/g, (match, name: string) => (name in vars ? String(vars[name]) : match));
}

export function translator(messages: Messages) {
  return (key: MessageKey, vars?: Vars) => format(messages[key] ?? en[key] ?? key, vars);
}

export type T = ReturnType<typeof translator>;
