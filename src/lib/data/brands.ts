import brands from "../../../data/normalized/brands.json";

export type Brand = {
  id: string;
  slug: string;
  name: string;
  modelCount: number;
  isFeatured: boolean;
  sources?: {
    zeroteknik?: boolean;
    solobu?: boolean;
  };
};

export function getAllBrands(): Brand[] {
  return brands as Brand[];
}

export function getFeaturedBrands(limit = 15): Brand[] {
  return getAllBrands().filter((b) => b.isFeatured).slice(0, limit);
}
