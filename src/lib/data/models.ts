// src/lib/data/models.ts
import modelsByBrand from "../../../data/normalized/models-by-brand.json";

export type Model = {
  id: string;
  brandId: string;
  modelCode: string;
  slug: string;
  screenType: "tv";
  sources: {
    zeroteknik: boolean;
    solobu: boolean;
  };
  note?: string;
};

type ModelsByBrand = Record<string, Model[]>;

export function getModelsByBrand(brandSlug: string): Model[] {
  const map = modelsByBrand as ModelsByBrand;
  return map[brandSlug] ?? [];
}

export function getAllBrandSlugs(): string[] {
  const map = modelsByBrand as ModelsByBrand;
  return Object.keys(map);
}
