// src/lib/seo.ts

type SeoInput = {
  title: string;
  description: string;
  canonical: string;
};

export function buildSeo(input: SeoInput) {
  // İleride template + schema + robots burada büyüyecek
  return {
    title: input.title,
    description: input.description,
    canonical: input.canonical,
  };
}