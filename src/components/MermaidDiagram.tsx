import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

interface MermaidDiagramProps {
  chart: string;
  className?: string;
  // Use loose typing to avoid depending on internal Mermaid types (which can shift)
  config?: Record<string, any>;
  onError?: (err: unknown) => void;
}

// Lightweight reusable Mermaid wrapper component
const MermaidDiagram: React.FC<MermaidDiagramProps> = ({ chart, className = '', config, onError }) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [svg, setSvg] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const render = async () => {
      try {
        setError(null);
        // Initialize once with provided config overrides
        mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', theme: 'dark', ...config });
        const id = 'mermaid-diagram-' + Math.random().toString(36).slice(2);
        const { svg } = await mermaid.render(id, chart);
        if (!cancelled) setSvg(svg);
      } catch (e) {
        const msg = e instanceof Error ? e.message : 'Unknown Mermaid error';
        setError(msg);
        onError?.(e);
      }
    };
    render();
    return () => { cancelled = true; };
  }, [chart, config, onError]);

  return (
    <div className={className}>
      {error && (
        <div className="p-3 mb-2 rounded bg-red-500/20 border border-red-500/40 text-red-300 text-sm">
          Mermaid render error: {error}
        </div>
      )}
      <div ref={containerRef} className="overflow-auto">
        {/* eslint-disable-next-line react/no-danger */}
        <div dangerouslySetInnerHTML={{ __html: svg }} />
      </div>
    </div>
  );
};

export default MermaidDiagram;
