import { cookies } from "next/headers";
import { LOCALE_COOKIE, defaultLocale, dictionaries, isLocale, translator, type Locale } from "./index";

/** Locale for the current request (cookie, else NEXT_PUBLIC_DEFAULT_LOCALE). Server components only. */
export async function getLocale(): Promise<Locale> {
  const value = (await cookies()).get(LOCALE_COOKIE)?.value;
  return isLocale(value) ? value : defaultLocale();
}

export async function getI18n() {
  const locale = await getLocale();
  return { locale, t: translator(dictionaries[locale]), messages: dictionaries[locale] };
}
