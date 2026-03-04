// src/lib/data.ts

import brandsRaw from "../../data/normalized/brands.json";
import modelsByBrandRaw from "../../data/normalized/models-by-brand.json";
import modelPanelMapRaw from "../../data/normalized/model-panel-map.json";

import type { Brand, ModelsByBrand, ModelSummary, ModelPanelMap, PanelRef } from "../types/catalog";

export const brands = brandsRaw as unknown as Brand[];
export const modelsByBrand = modelsByBrandRaw as unknown as ModelsByBrand;
export const modelPanelMap = modelPanelMapRaw as unknown as ModelPanelMap;

/** ✅ Dynamic routes için brand listesi */
export function getAllBrands(): Brand[] {
  return brands;
}

export function getBrandBySlug(brandSlug: string): Brand | undefined {
  return brands.find((b) => b.slug === brandSlug);
}

export function getModelsForBrand(brandSlug: string): ModelSummary[] {
  return modelsByBrand[brandSlug] ?? [];
}

export function getModel(brandSlug: string, modelSlug: string): ModelSummary | undefined {
  return getModelsForBrand(brandSlug).find((m) => m.slug === modelSlug);
}

export function makeModelKey(brandSlug: string, modelSlug: string): string {
  return `${brandSlug}__${modelSlug}`;
}

export function getPanelsForModel(brandSlug: string, modelSlug: string): PanelRef[] {
  const key = makeModelKey(brandSlug, modelSlug);
  return modelPanelMap[key] ?? [];
}