import { useState } from "react";
import { mockPullRequests, type PullRequest } from "@/lib/mock-data";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Button } from "@/components/ui/button";
import { GitPullRequest, Plus, Minus, ChevronRight, Check, MessageSquare } from "lucide-react";

const prStatusVariant = (s: PullRequest["status"]) =>
  s === "open" ? "primary" : s === "merged" ? "success" : "default";

export default function PullRequestsPage() {
  const [selected, setSelected] = useState<PullRequest | null>(null);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Pull Requests</h1>
        <p className="mt-1 text-sm text-muted-foreground">AI-powered code reviews for your pull requests</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        {/* PR List */}
        <div className="lg:col-span-2 space-y-2">
          {mockPullRequests.map((pr) => (
            <button
              key={pr.id}
              onClick={() => setSelected(pr)}
              className={`w-full rounded-xl border p-4 text-left transition-colors ${
                selected?.id === pr.id
                  ? "border-primary bg-primary/5"
                  : "border-border bg-card hover:border-primary/30"
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-2">
                  <GitPullRequest className="mt-0.5 h-4 w-4 text-muted-foreground shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-card-foreground">{pr.title}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {pr.author} · {pr.repository} · {pr.createdAt}
                    </p>
                  </div>
                </div>
                <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
              </div>
              <div className="mt-2 flex items-center gap-3">
                <StatusBadge status={pr.status} variant={prStatusVariant(pr.status)} />
                <span className="flex items-center gap-1 text-xs text-success"><Plus className="h-3 w-3" />{pr.additions}</span>
                <span className="flex items-center gap-1 text-xs text-destructive"><Minus className="h-3 w-3" />{pr.deletions}</span>
              </div>
            </button>
          ))}
        </div>

        {/* PR Detail */}
        <div className="lg:col-span-3">
          {selected ? (
            <div className="rounded-xl border border-border bg-card p-6 space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-card-foreground">{selected.title}</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  by {selected.author} · {selected.createdAt} · {selected.repository}
                </p>
              </div>

              {/* Diff preview */}
              <div className="rounded-lg border border-border bg-muted p-4">
                <p className="text-xs font-medium text-muted-foreground mb-2">Diff Summary</p>
                <div className="flex gap-4 text-sm">
                  <span className="text-success">+{selected.additions} additions</span>
                  <span className="text-destructive">-{selected.deletions} deletions</span>
                </div>
              </div>

              {/* AI Review */}
              {selected.aiSummary && (
                <div className="rounded-lg border border-primary/20 bg-primary/5 p-4">
                  <p className="text-xs font-medium text-primary mb-2">AI Review Summary</p>
                  <p className="text-sm text-card-foreground leading-relaxed">{selected.aiSummary}</p>
                </div>
              )}

              {/* Suggestions */}
              {selected.suggestedChanges && (
                <div>
                  <p className="text-sm font-medium text-card-foreground mb-3">Suggested Changes</p>
                  <ul className="space-y-2">
                    {selected.suggestedChanges.map((change, i) => (
                      <li key={i} className="flex items-start gap-2 rounded-lg border border-border bg-muted p-3 text-sm text-card-foreground">
                        <MessageSquare className="mt-0.5 h-4 w-4 text-primary shrink-0" />
                        {change}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <Button className="gap-2"><Check className="h-4 w-4" /> Approve</Button>
                <Button variant="outline">Request Changes</Button>
              </div>
            </div>
          ) : (
            <div className="flex h-64 items-center justify-center rounded-xl border border-dashed border-border">
              <p className="text-sm text-muted-foreground">Select a pull request to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
