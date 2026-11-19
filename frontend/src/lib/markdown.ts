/** Lightweight markdown → HTML for assistant chat replies (bold, lists, headings). */

export type MdBlock =
  | { type: "heading"; level: 1 | 2 | 3; text: string }
  | { type: "paragraph"; text: string }
  | { type: "ul"; items: string[] }
  | { type: "ol"; items: string[] }
  | { type: "code"; text: string };

export type MdInline =
  | { type: "text"; value: string }
  | { type: "strong"; value: string }
  | { type: "em"; value: string }
  | { type: "code"; value: string };

/** Parse inline emphasis: **bold**, *italic*, `code` (no nesting). */
export function parseInline(text: string): MdInline[] {
  const out: MdInline[] = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) {
      out.push({ type: "text", value: text.slice(last, m.index) });
    }
    const token = m[0];
    if (token.startsWith("**") && token.endsWith("**")) {
      out.push({ type: "strong", value: token.slice(2, -2) });
    } else if (token.startsWith("`") && token.endsWith("`")) {
      out.push({ type: "code", value: token.slice(1, -1) });
    } else if (token.startsWith("*") && token.endsWith("*")) {
      out.push({ type: "em", value: token.slice(1, -1) });
    } else {
      out.push({ type: "text", value: token });
    }
    last = m.index + token.length;
  }
  if (last < text.length) {
    out.push({ type: "text", value: text.slice(last) });
  }
  return out.length ? out : [{ type: "text", value: text }];
}

export function parseMarkdown(source: string): MdBlock[] {
  const lines = (source || "").replace(/\r\n/g, "\n").split("\n");
  const blocks: MdBlock[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (!line.trim()) {
      i += 1;
      continue;
    }

    if (line.startsWith("```")) {
      const buf: string[] = [];
      i += 1;
      while (i < lines.length && !lines[i].startsWith("```")) {
        buf.push(lines[i]);
        i += 1;
      }
      if (i < lines.length) i += 1;
      blocks.push({ type: "code", text: buf.join("\n") });
      continue;
    }

    const heading = /^(#{1,3})\s+(.+)$/.exec(line);
    if (heading) {
      blocks.push({
        type: "heading",
        level: heading[1].length as 1 | 2 | 3,
        text: heading[2].trim(),
      });
      i += 1;
      continue;
    }

    if (/^[-*]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^[-*]\s+/, "").trim());
        i += 1;
      }
      blocks.push({ type: "ul", items });
      continue;
    }

    if (/^\d+\.\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\d+\.\s+/, "").trim());
        i += 1;
      }
      blocks.push({ type: "ol", items });
      continue;
    }

    const para: string[] = [line];
    i += 1;
    while (
      i < lines.length &&
      lines[i].trim() &&
      !lines[i].startsWith("#") &&
      !/^[-*]\s+/.test(lines[i]) &&
      !/^\d+\.\s+/.test(lines[i]) &&
      !lines[i].startsWith("```")
    ) {
      para.push(lines[i]);
      i += 1;
    }
    blocks.push({ type: "paragraph", text: para.join(" ") });
  }

  return blocks;
}
