// src/lib/data.ts
import brandsRaw from "../../data/normalized/brands.json";
import modelsByBrandRaw from "../../data/normalized/models-by-brand.json";
import modelPanelMapRaw from "../../data/normalized/model-panel-map.json"; // yoksa dosyayı oluştur (boş {})

import type { Brand, ModelsByBrand, ModelSummary, ModelPanelMap, PanelRef } from "../types/catalog";

// Astro/Vite JSON importları genelde already-typed değil; burada cast ediyoruz.
export const brands = brandsRaw as Brand[];
export const modelsByBrand = modelsByBrandRaw as ModelsByBrand;
export const modelPanelMap = modelPanelMapRaw as ModelPanelMap;

export function getBrandBySlug(brandSlug: string): Brand | undefined {
  return brands.find((b) => b.slug === brandSlug);
}

export function getModelsForBrand(brandSlug: string): ModelSummary[] {
  return modelsByBrand[brandSlug] ?? [];
}

export function getModel(brandSlug: string, modelSlug: string): ModelSummary | undefined {
  const list = getModelsForBrand(brandSlug);
  return list.find((m) => m.slug === modelSlug);
}

export function makeModelKey(brandSlug: string, modelSlug: string): string {
  return `${brandSlug}__${modelSlug}`;
}

export function getPanelsForModel(brandSlug: string, modelSlug: string): PanelRef[] {
  const key = makeModelKey(brandSlug, modelSlug);
  return modelPanelMap[key] ?? [];
}