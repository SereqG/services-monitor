import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { cookies } from "next/headers";
import "./globals.css";
import { LanguageProvider } from "@/lib/i18n";
import { LANGUAGE_COOKIE, isLanguage, type Language } from "@/lib/i18n";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Velocity.Lab — Real-time Web Performance Analysis",
  description:
    "Analyze Core Web Vitals, SEO, accessibility and content health in a single pass.",
  openGraph: {
    title: "Velocity.Lab — Real-time Web Performance Analysis",
    description:
      "Analyze Core Web Vitals, SEO, accessibility and content health in a single pass.",
  },
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const cookieStore = await cookies();
  const cookieLang = cookieStore.get(LANGUAGE_COOKIE)?.value;
  const lang: Language = isLanguage(cookieLang) ? cookieLang : "en";

  return (
    <html lang={lang} className={`${inter.variable} ${jetbrainsMono.variable} h-full antialiased`}>
      <body className="min-h-full">
        <LanguageProvider initialLanguage={lang}>{children}</LanguageProvider>
      </body>
    </html>
  );
}
