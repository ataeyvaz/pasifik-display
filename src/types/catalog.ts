// src/types/catalog.ts

export type Brand = {
  slug: string;
  name: string;
  modelCount: number;
  isFeatured?: boolean;
};

export type ModelSummary = {
  id: string;
  brandId: string;       // JSON’da var
  modelCode: string;     // JSON’da var
  slug: string;          // JSON’da var
  screenType?: string;   // JSON’da var
  sources?: {
    zeroteknik?: boolean;
    solobu?: boolean;
  };
  note?: string;         // JSON’da bazen var
  isFeatured?: boolean;  // varsa kalsın
};

export type ModelsByBrand = Record<string, ModelSummary[]>;

export type PanelRef = {
  panelCode: string;
  note?: string;
  confidence?: "low" | "medium" | "high";
};

export type ModelPanelMap = Record<string, PanelRef[]>;