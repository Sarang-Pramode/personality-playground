import { parseInline, parseMarkdown, type MdInline } from "../lib/markdown";

function Inline({ parts }: { parts: MdInline[] }) {
  return (
    <>
      {parts.map((p, i) => {
        if (p.type === "strong") {
          return (
            <strong key={i} className="font-semibold text-slate-900">
              {p.value}
            </strong>
          );
        }
        if (p.type === "em") {
          return (
            <em key={i} className="italic">
              {p.value}
            </em>
          );
        }
        if (p.type === "code") {
          return (
            <code
              key={i}
              className="rounded bg-slate-200/80 px-1 py-0.5 font-mono text-[0.85em]"
            >
              {p.value}
            </code>
          );
        }
        return <span key={i}>{p.value}</span>;
      })}
    </>
  );
}

/** Renders assistant markdown (headings, lists, bold/italic/code). */
export function MarkdownContent({ content }: { content: string }) {
  const blocks = parseMarkdown(content);
  if (!blocks.length) {
    return <span className="text-[var(--muted)]">(empty)</span>;
  }

  return (
    <div className="markdown-body space-y-2 leading-relaxed">
      {blocks.map((b, i) => {
        if (b.type === "heading") {
          const Tag = b.level === 1 ? "h3" : b.level === 2 ? "h4" : "h5";
          return (
            <Tag
              key={i}
              className="font-semibold text-slate-900"
            >
              <Inline parts={parseInline(b.text)} />
            </Tag>
          );
        }
        if (b.type === "ul") {
          return (
            <ul key={i} className="list-disc space-y-1 pl-5">
              {b.items.map((item, j) => (
                <li key={j}>
                  <Inline parts={parseInline(item)} />
                </li>
              ))}
            </ul>
          );
        }
        if (b.type === "ol") {
          return (
            <ol key={i} className="list-decimal space-y-1 pl-5">
              {b.items.map((item, j) => (
                <li key={j}>
                  <Inline parts={parseInline(item)} />
                </li>
              ))}
            </ol>
          );
        }
        if (b.type === "code") {
          return (
            <pre
              key={i}
              className="overflow-x-auto rounded bg-slate-900/90 p-2 font-mono text-[11px] text-slate-100"
            >
              {b.text}
            </pre>
          );
        }
        return (
          <p key={i}>
            <Inline parts={parseInline(b.text)} />
          </p>
        );
      })}
    </div>
  );
}
