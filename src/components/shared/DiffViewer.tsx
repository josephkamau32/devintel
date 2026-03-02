import { useState } from "react";
import { ChevronDown, ChevronRight, FileCode } from "lucide-react";

interface DiffViewerProps {
    diff: string;
    maxHeightPx?: number;
}

interface DiffFile {
    header: string;
    fromFile: string;
    toFile: string;
    hunks: DiffHunk[];
}

interface DiffHunk {
    header: string;
    lines: DiffLine[];
}

interface DiffLine {
    type: "added" | "removed" | "context" | "noNewline";
    content: string;
    oldLineNo?: number;
    newLineNo?: number;
}

/** Parse a raw unified diff into structured file + hunk objects */
function parseDiff(raw: string): DiffFile[] {
    const files: DiffFile[] = [];
    let currentFile: DiffFile | null = null;
    let currentHunk: DiffHunk | null = null;
    let oldLine = 0;
    let newLine = 0;

    for (const raw_line of raw.split("\n")) {
        if (raw_line.startsWith("diff --git")) {
            if (currentFile) files.push(currentFile);
            currentFile = { header: raw_line, fromFile: "", toFile: "", hunks: [] };
            currentHunk = null;
            continue;
        }

        if (!currentFile) continue;

        if (raw_line.startsWith("--- ")) {
            currentFile.fromFile = raw_line.slice(4).replace(/^a\//, "");
            continue;
        }
        if (raw_line.startsWith("+++ ")) {
            currentFile.toFile = raw_line.slice(4).replace(/^b\//, "");
            continue;
        }

        if (raw_line.startsWith("@@")) {
            // e.g. @@ -1,6 +1,8 @@
            const match = raw_line.match(/@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
            oldLine = match ? parseInt(match[1]) : 0;
            newLine = match ? parseInt(match[2]) : 0;
            currentHunk = { header: raw_line, lines: [] };
            currentFile.hunks.push(currentHunk);
            continue;
        }

        if (!currentHunk) continue;

        if (raw_line.startsWith("+")) {
            currentHunk.lines.push({ type: "added", content: raw_line.slice(1), newLineNo: newLine++ });
        } else if (raw_line.startsWith("-")) {
            currentHunk.lines.push({ type: "removed", content: raw_line.slice(1), oldLineNo: oldLine++ });
        } else if (raw_line.startsWith("\\ No newline")) {
            currentHunk.lines.push({ type: "noNewline", content: raw_line });
        } else {
            currentHunk.lines.push({
                type: "context",
                content: raw_line.slice(1),
                oldLineNo: oldLine++,
                newLineNo: newLine++,
            });
        }
    }

    if (currentFile) files.push(currentFile);
    return files;
}

function DiffLineRow({ line }: { line: DiffLine }) {
    const bg =
        line.type === "added"
            ? "bg-green-500/10 border-l-2 border-green-500"
            : line.type === "removed"
                ? "bg-red-500/10 border-l-2 border-red-500"
                : "border-l-2 border-transparent";

    const prefix =
        line.type === "added" ? "+" : line.type === "removed" ? "-" : " ";

    const prefixColor =
        line.type === "added"
            ? "text-green-400"
            : line.type === "removed"
                ? "text-red-400"
                : "text-muted-foreground";

    return (
        <div className={`flex font-mono text-xs leading-5 ${bg}`}>
            <span className="w-10 shrink-0 select-none pr-2 text-right text-muted-foreground/50 py-0.5 px-2">
                {line.oldLineNo ?? ""}
            </span>
            <span className="w-10 shrink-0 select-none pr-2 text-right text-muted-foreground/50 py-0.5 px-2">
                {line.newLineNo ?? ""}
            </span>
            <span className={`w-5 shrink-0 select-none text-center py-0.5 ${prefixColor}`}>
                {prefix}
            </span>
            <span className="flex-1 whitespace-pre-wrap break-all py-0.5 pr-3 text-foreground">
                {line.content}
            </span>
        </div>
    );
}

function DiffFileBlock({ file }: { file: DiffFile }) {
    const [collapsed, setCollapsed] = useState(false);
    const addCount = file.hunks.flatMap(h => h.lines).filter(l => l.type === "added").length;
    const removeCount = file.hunks.flatMap(h => h.lines).filter(l => l.type === "removed").length;
    const name = file.toFile || file.fromFile || file.header;

    return (
        <div className="rounded-lg border border-border overflow-hidden mb-3">
            {/* File header */}
            <button
                onClick={() => setCollapsed(c => !c)}
                className="flex w-full items-center gap-2 bg-muted px-3 py-2 text-left hover:bg-accent transition-colors"
            >
                {collapsed ? (
                    <ChevronRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                ) : (
                    <ChevronDown className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                )}
                <FileCode className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                <span className="flex-1 min-w-0 truncate text-xs font-mono text-foreground">{name}</span>
                <span className="shrink-0 text-xs text-green-500">+{addCount}</span>
                <span className="ml-1 shrink-0 text-xs text-red-500">-{removeCount}</span>
            </button>

            {!collapsed && (
                <div className="overflow-x-auto">
                    {file.hunks.map((hunk, i) => (
                        <div key={i}>
                            <div className="bg-blue-500/5 px-3 py-0.5 text-[10px] font-mono text-blue-400 border-y border-blue-500/20">
                                {hunk.header}
                            </div>
                            {hunk.lines.map((line, j) => (
                                <DiffLineRow key={j} line={line} />
                            ))}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export function DiffViewer({ diff, maxHeightPx = 480 }: DiffViewerProps) {
    const files = parseDiff(diff);

    if (!diff || files.length === 0) {
        return (
            <div className="flex items-center justify-center py-10 text-sm text-muted-foreground">
                No diff available for this pull request.
            </div>
        );
    }

    const totalAdded = files.flatMap(f => f.hunks).flatMap(h => h.lines).filter(l => l.type === "added").length;
    const totalRemoved = files.flatMap(f => f.hunks).flatMap(h => h.lines).filter(l => l.type === "removed").length;

    return (
        <div>
            {/* Summary bar */}
            <div className="mb-3 flex items-center gap-3 text-xs text-muted-foreground">
                <span>{files.length} file{files.length !== 1 ? "s" : ""} changed</span>
                <span className="text-green-500">+{totalAdded}</span>
                <span className="text-red-500">-{totalRemoved}</span>
            </div>
            <div style={{ maxHeight: maxHeightPx }} className="overflow-auto">
                {files.map((file, i) => (
                    <DiffFileBlock key={i} file={file} />
                ))}
            </div>
        </div>
    );
}
