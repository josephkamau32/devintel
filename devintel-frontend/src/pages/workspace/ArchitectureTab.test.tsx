import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, waitFor } from '@testing-library/react';
import { ArchitectureTab } from './ArchitectureTab';

const mockInitialize = vi.fn();
const mockRender = vi.fn().mockResolvedValue({ svg: '<svg data-testid="rendered-svg"></svg>' });

vi.mock('mermaid', () => ({
  default: {
    initialize: mockInitialize,
    render: mockRender,
  },
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useOutletContext: () => ({
      repository: {
        id: 'repo-1',
        repo_name: 'devintel',
        full_name: 'josephkamau32/devintel',
        indexing_status: 'complete',
      },
    }),
  };
});

vi.mock('../../hooks/useAPI', () => ({
  useArchitectureDiagrams: () => ({
    data: {
      diagrams: [
        {
          id: 'diag-1',
          name: 'Architecture',
          diagram_type: 'mermaid',
          mermaid_code: 'graph TD\n    subgraph a_b_39a01277["a#quot;b"]\n        Foo["Foo"]\n    end',
        },
      ],
    },
    isLoading: false,
  }),
  useGenerateDiagram: () => ({
    isPending: false,
    mutateAsync: vi.fn(),
  }),
}));

describe('ArchitectureTab', () => {
  beforeEach(() => {
    mockInitialize.mockClear();
    mockRender.mockClear();
  });

  it('initializes mermaid with explicit securityLevel: strict', async () => {
    render(<ArchitectureTab />);

    await waitFor(() => {
      expect(mockInitialize).toHaveBeenCalledWith(
        expect.objectContaining({
          startOnLoad: false,
          securityLevel: 'strict',
        }),
      );
    });
  });

  it('real mermaid parser accepts sanitized hostile diagram output', async () => {
    const actualMermaid = (await vi.importActual<typeof import('mermaid')>('mermaid')).default;
    actualMermaid.initialize({ startOnLoad: false, securityLevel: 'strict' });
    const sanitizedDiagram = [
      'graph TD',
      '    subgraph a_b_39a01277["a#quot;b"]',
      '        a_b__Foo_a0aaea2d["Foo"]',
      '    end',
      '    subgraph img_src_x_onerror_alert_1_63b586b4["#lt;img src=x onerror=alert(1)#gt;"]',
      '        img_src_x_onerror_alert_1___run_db0d823b("run()")',
      '    end',
    ].join('\n');

    const parsed = await actualMermaid.parse(sanitizedDiagram);
    expect(parsed).toBeTruthy();
  }, 20000);
});
