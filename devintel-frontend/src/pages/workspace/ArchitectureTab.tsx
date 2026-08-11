import { useEffect, useRef, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useArchitectureDiagrams, useGenerateDiagram } from '../../hooks/useAPI';
import type { Repository } from '../../types/repository';
import { Network, Plus, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';

export function ArchitectureTab() {
  const { repository } = useOutletContext<{ repository: Repository }>();
  const { data: diagramsData, isLoading } = useArchitectureDiagrams(repository.id);
  const generateDiagram = useGenerateDiagram();
  const [selectedType, setSelectedType] = useState('mermaid');
  const mermaidRef = useRef<HTMLDivElement>(null);
  const [renderedSvg, setRenderedSvg] = useState<string>('');
  const [selectedDiagramCode, setSelectedDiagramCode] = useState<string>('');

  const isIndexed = repository.indexing_status === 'completed' || repository.indexing_status === 'complete';

  // Render mermaid diagram
  useEffect(() => {
    if (!selectedDiagramCode) {
      setRenderedSvg('');
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const mermaid = (await import('mermaid')).default;
        mermaid.initialize({
          startOnLoad: false,
          theme: 'dark',
          themeVariables: {
            darkMode: true,
            background: '#111114',
            primaryColor: '#4f46e5',
            primaryTextColor: '#fafafa',
            lineColor: '#52525b',
          },
        });
        const { svg } = await mermaid.render('mermaid-diagram', selectedDiagramCode);
        if (!cancelled) setRenderedSvg(svg);
      } catch (e) {
        if (!cancelled) setRenderedSvg('');
      }
    })();

    return () => { cancelled = true; };
  }, [selectedDiagramCode]);

  // Auto-select first diagram
  useEffect(() => {
    if (diagramsData?.diagrams?.length && !selectedDiagramCode) {
      setSelectedDiagramCode(diagramsData.diagrams[0].mermaid_code);
    }
  }, [diagramsData, selectedDiagramCode]);

  const handleGenerate = async () => {
    try {
      const result = await generateDiagram.mutateAsync({
        repositoryId: repository.id,
        diagramType: selectedType,
      });
      setSelectedDiagramCode(result.diagram.mermaid_code);
      toast.success('Architecture diagram generated!');
    } catch {
      toast.error('Failed to generate diagram. Ensure the repository is indexed.');
    }
  };

  if (!isIndexed) {
    return (
      <div className="card p-10 text-center animate-fade-in">
        <Network className="h-8 w-8 text-text-quaternary mx-auto mb-4" />
        <h2 className="text-h3 text-text-primary mb-2">Index required</h2>
        <p className="text-body text-text-tertiary max-w-md mx-auto">
          Index this repository to generate architecture diagrams.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
        <select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
          className="text-sm bg-surface-3 border border-border-medium rounded-lg px-3 py-2 text-text-primary outline-none focus:border-brand-500"
        >
          <option value="mermaid">Mermaid Diagram</option>
          <option value="c4_context">C4 Context</option>
          <option value="c4_container">C4 Container</option>
          <option value="c4_component">C4 Component</option>
        </select>
        <button
          onClick={handleGenerate}
          disabled={generateDiagram.isPending}
          className="flex items-center gap-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all"
        >
          {generateDiagram.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin-slow" />
          ) : (
            <Plus className="h-4 w-4" />
          )}
          Generate Diagram
        </button>
      </div>

      {/* Existing diagrams list */}
      {isLoading ? (
        <div className="card p-6 text-center">
          <Loader2 className="h-5 w-5 text-brand-400 animate-spin-slow mx-auto" />
        </div>
      ) : diagramsData?.diagrams && diagramsData.diagrams.length > 0 ? (
        <div className="flex gap-2 overflow-x-auto no-scrollbar">
          {diagramsData.diagrams.map((d) => (
            <button
              key={d.id}
              onClick={() => setSelectedDiagramCode(d.mermaid_code)}
              className={`action-pill whitespace-nowrap ${selectedDiagramCode === d.mermaid_code ? 'border-brand-500 text-brand-400 bg-brand-600/10' : ''}`}
            >
              <Network className="h-3 w-3" />
              {d.name || d.diagram_type}
            </button>
          ))}
        </div>
      ) : null}

      {/* Diagram render */}
      {selectedDiagramCode ? (
        <div className="card overflow-hidden">
          <div className="px-5 py-3 border-b border-border flex items-center justify-between">
            <h3 className="text-sm font-semibold text-text-primary">Architecture Diagram</h3>
            <button
              onClick={() => {
                navigator.clipboard.writeText(selectedDiagramCode);
                toast.success('Mermaid code copied!');
              }}
              className="text-xs text-text-tertiary hover:text-text-secondary transition-colors"
            >
              Copy code
            </button>
          </div>
          {renderedSvg ? (
            <div
              ref={mermaidRef}
              className="p-6 overflow-x-auto bg-surface-1"
              dangerouslySetInnerHTML={{ __html: renderedSvg }}
            />
          ) : (
            <div className="p-6">
              <pre className="text-xs text-text-tertiary overflow-x-auto bg-surface-3 p-4 rounded-lg border border-border">
                {selectedDiagramCode}
              </pre>
            </div>
          )}
        </div>
      ) : !generateDiagram.isPending ? (
        <div className="card p-10 text-center">
          <Network className="h-8 w-8 text-text-quaternary mx-auto mb-4" />
          <p className="text-sm text-text-tertiary">
            No architecture diagrams yet. Click "Generate Diagram" to analyze the codebase structure.
          </p>
        </div>
      ) : null}
    </div>
  );
}
