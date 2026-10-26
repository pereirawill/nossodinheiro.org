/** "UNIÃO" → "uniao", "PC do B" → "pc-do-b". Usado nas URLs /deputados/uf/ e /deputados/partido/. */
export const slug = (s: string) =>
  s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
