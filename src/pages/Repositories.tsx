import { useState } from "react";
import { Plus, Search, MoreHorizontal, RefreshCw, Eye, Trash2, Github } from "lucide-react";
import { mockRepositories, type Repository } from "@/lib/mock-data";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Button } from "@/components/ui/button";

const statusVariant = (s: Repository["status"]) =>
  s === "indexed" ? "success" : s === "indexing" ? "warning" : "default";

const statusLabel = (s: Repository["status"]) =>
  s === "indexed" ? "Indexed" : s === "indexing" ? "Indexing..." : "Not Indexed";

export default function RepositoriesPage() {
  const [repos] = useState(mockRepositories);
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);

  const filtered = repos.filter((r) => r.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">My Repositories</h1>
          <p className="mt-1 text-sm text-muted-foreground">Manage and index your GitHub repositories</p>
        </div>
        <Button className="gap-2" onClick={() => setShowModal(true)}>
          <Github className="h-4 w-4" /> Connect Repository
        </Button>
      </div>

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search repositories..."
          className="h-9 w-full rounded-md border border-input bg-accent pl-9 pr-4 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-primary transition-colors"
        />
      </div>

      <div className="overflow-hidden rounded-xl border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted">
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Repository</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Status</th>
              <th className="hidden px-4 py-3 text-left font-medium text-muted-foreground sm:table-cell">Language</th>
              <th className="hidden px-4 py-3 text-left font-medium text-muted-foreground md:table-cell">Last Updated</th>
              <th className="px-4 py-3 text-right font-medium text-muted-foreground">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((repo) => (
              <tr key={repo.id} className="border-b border-border last:border-0 hover:bg-accent/50 transition-colors">
                <td className="px-4 py-3">
                  <div>
                    <p className="font-medium text-foreground">{repo.name}</p>
                    <p className="text-xs text-muted-foreground">{repo.fullName}</p>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={statusLabel(repo.status)} variant={statusVariant(repo.status)} />
                </td>
                <td className="hidden px-4 py-3 text-muted-foreground sm:table-cell">{repo.language}</td>
                <td className="hidden px-4 py-3 text-muted-foreground md:table-cell">{repo.lastUpdated}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-1">
                    <button className="rounded p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors">
                      <RefreshCw className="h-4 w-4" />
                    </button>
                    <button className="rounded p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors">
                      <Eye className="h-4 w-4" />
                    </button>
                    <button className="rounded p-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg animate-slide-up">
            <h2 className="text-lg font-semibold text-card-foreground">Connect GitHub Repository</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Enter the repository URL or select from your GitHub account.
            </p>
            <input
              type="text"
              placeholder="https://github.com/owner/repo"
              className="mt-4 h-9 w-full rounded-md border border-input bg-accent px-3 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-primary transition-colors"
            />
            <div className="mt-6 flex justify-end gap-3">
              <Button variant="outline" onClick={() => setShowModal(false)}>Cancel</Button>
              <Button onClick={() => setShowModal(false)}>Start Indexing</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
