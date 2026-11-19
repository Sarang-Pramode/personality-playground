import { describe, expect, it } from "vitest";
import { parseInline, parseMarkdown } from "./markdown";

describe("parseInline", () => {
  it("parses bold and italic", () => {
    const parts = parseInline("Hello **world** and *there*");
    expect(parts).toEqual([
      { type: "text", value: "Hello " },
      { type: "strong", value: "world" },
      { type: "text", value: " and " },
      { type: "em", value: "there" },
    ]);
  });

  it("parses inline code", () => {
    const parts = parseInline("Use `get_rewards_balance`");
    expect(parts.some((p) => p.type === "code" && p.value === "get_rewards_balance")).toBe(
      true,
    );
  });
});

describe("parseMarkdown", () => {
  it("parses headings lists and paragraphs", () => {
    const blocks = parseMarkdown(
      "# Title\n\nA **bold** line\n\n- one\n- two\n\n1. first\n2. second\n",
    );
    expect(blocks[0]).toEqual({ type: "heading", level: 1, text: "Title" });
    expect(blocks.some((b) => b.type === "ul")).toBe(true);
    expect(blocks.some((b) => b.type === "ol")).toBe(true);
    const para = blocks.find((b) => b.type === "paragraph");
    expect(para && para.type === "paragraph" && para.text.includes("bold")).toBe(
      true,
    );
  });

  it("does not leave raw hashes as the only rendering path", () => {
    const blocks = parseMarkdown("## Eligibility\n\n### Steps");
    expect(blocks.filter((b) => b.type === "heading")).toHaveLength(2);
  });
});
