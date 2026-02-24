import rawModelsByBrand from "../../../data/normalized/models-by-brand.json";

export type ModelSources = {
  zeroteknik: boolean;
  solobu: boolean;
};

export type ModelItem = {
  id: string;
  brandId: string;
  modelCode: string;
  slug: string;
  screenType: "tv" | "unknown";
  sources: ModelSources; // ✅ runtime'da hep var
  note?: string;
};

// ✅ Buradaki parantez kritik: Record<string, ( ... )[]>
type ModelsByBrand = Record<
  string,
  (Omit<ModelItem, "sources"> & { sources?: Partial<ModelSources> })[]
>;

// ✅ TS “overlap” hatasını kesmek için unknown üzerinden cast
const RAW = rawModelsByBrand as unknown as ModelsByBrand;

const DEFAULT_SOURCES: ModelSources = { zeroteknik: false, solobu: false };

function normalizeModel(m: any, brandSlug: string): ModelItem {
  const s = (m?.sources ?? {}) as Partial<ModelSources>;

  const rawScreenType = String(m?.screenType ?? "");
  const screenType: "tv" | "unknown" = rawScreenType === "tv" ? "tv" : "unknown";

  return {
    id: String(m?.id ?? `${brandSlug}:${m?.modelCode ?? "unknown"}`),
    brandId: String(m?.brandId ?? brandSlug),
    modelCode: String(m?.modelCode ?? ""),
    slug: String(m?.slug ?? ""),
    screenType,
    sources: {
      zeroteknik: Boolean(s.zeroteknik ?? DEFAULT_SOURCES.zeroteknik),
      solobu: Boolean(s.solobu ?? DEFAULT_SOURCES.solobu),
    },
    note: m?.note ? String(m.note) : undefined,
  };
}

export function getModelsByBrand(brandSlug: string): ModelItem[] {
  const list = RAW[brandSlug] ?? [];
  return list.map((m) => normalizeModel(m, brandSlug));
}

export function getAllBrandSlugs(): string[] {
  return Object.keys(RAW).sort();
}

export function getAllModelPaths(): { brand: string; model: string }[] {
  const out: { brand: string; model: string }[] = [];
  for (const brand of Object.keys(RAW)) {
    const list = RAW[brand] ?? [];
    for (const m of list) {
      const slug = String((m as any)?.slug ?? "");
      if (slug) out.push({ brand, model: slug });
    }
  }
  return out;
}

export function getModelByBrandAndSlug(
  brandSlug: string,
  modelSlug: string
): ModelItem | null {
  const list = getModelsByBrand(brandSlug);
  return list.find((m) => m.slug === modelSlug) ?? null;
}
