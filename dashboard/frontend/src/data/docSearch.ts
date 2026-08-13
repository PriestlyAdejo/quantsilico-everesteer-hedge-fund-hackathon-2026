import type { DocArticle, DocBlock } from "./types";

export function articleSearchHaystack(article: DocArticle): string {
  const parts: string[] = [article.title, article.description];
  for (const block of article.blocks) {
    parts.push(...blockSearchParts(block));
  }
  return parts.join(" ").toLowerCase();
}

export function articleMatchesQuery(article: DocArticle, query: string): boolean {
  if (!query) return true;
  return articleSearchHaystack(article).includes(query.toLowerCase());
}

function blockSearchParts(block: DocBlock): string[] {
  switch (block.kind) {
    case "intro":
    case "heading":
    case "paragraph":
      return [block.text];
    case "callout":
      return [block.text];
    case "command":
      return [block.command];
    case "metric":
      return [block.name, block.text];
    case "related":
      return [block.href, block.label];
    case "flow":
      return block.nodes.map((n) => n.label);
    case "table":
      return [...block.headers, ...block.rows.flat()];
  }
}
