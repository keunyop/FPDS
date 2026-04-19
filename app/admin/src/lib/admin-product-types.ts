import type { ProductTypeItem } from "@/lib/admin-api";

export type AdminProductTypeOption = {
  label: string;
  value: string;
  description: string;
  builtIn: boolean;
};

export function buildAdminProductTypeOptions(productTypes: ProductTypeItem[]): AdminProductTypeOption[] {
  return productTypes.map((item) => ({
    label: item.display_name,
    value: item.product_type_code,
    description: item.description,
    builtIn: item.built_in_flag,
  }));
}

export function buildAdminProductTypeLabelMap(productTypes: ProductTypeItem[]) {
  return Object.fromEntries(productTypes.map((item) => [item.product_type_code, item.display_name]));
}

export function formatAdminProductType(
  productType: string,
  labelMap?: Record<string, string>,
) {
  return labelMap?.[productType] ?? humanizeProductType(productType);
}

function humanizeProductType(productType: string) {
  return productType
    .split("-")
    .filter(Boolean)
    .map((part) => (part.toLowerCase() === "gic" ? "GIC" : `${part.slice(0, 1).toUpperCase()}${part.slice(1)}`))
    .join(" ");
}
