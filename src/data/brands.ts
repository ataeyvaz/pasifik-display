export interface Brand {
  slug: string;
  name: string;
  modelCount: number;
}

export const brands: Brand[] = [
  { slug: "philips", name: "Philips", modelCount: 124 },
  { slug: "samsung", name: "Samsung", modelCount: 243 },
  { slug: "lg", name: "LG", modelCount: 198 },
  { slug: "grundig", name: "Grundig", modelCount: 88 },
  { slug: "beko", name: "Beko", modelCount: 76 },
  { slug: "arcelik", name: "Arçelik", modelCount: 95 },
  { slug: "telefunken", name: "Telefunken", modelCount: 41 },
  { slug: "tcl", name: "TCL", modelCount: 109 },
  { slug: "blaupunkt", name: "Blaupunkt", modelCount: 37 },
  { slug: "sony", name: "Sony", modelCount: 155 },
  { slug: "vestel", name: "Vestel", modelCount: 164 },
  { slug: "sharp", name: "Sharp", modelCount: 52 },
  { slug: "toshiba", name: "Toshiba", modelCount: 67 }
];
