import React, { useEffect, useMemo, useRef, useState } from 'react';
import * as d3 from 'd3';

type TreeNode = {
  job_id: string;
  depth: number;
  status: string;
  children?: TreeNode[];
};

type Props = {
  root: TreeNode;
  width?: number;
  height?: number;
};

const STATUS_COLOR: Record<string, string> = {
  pending: '#9aa0a6',
  running: '#4285f4',
  completed: '#34a853',
  failed: '#ea4335',
  canceled: '#fbbc05',
};

export const HierarchyVisualization: React.FC<Props> = ({ root, width = 800, height = 480 }) => {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});

  const data = useMemo(() => root, [root]);

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const layout = d3.tree<TreeNode>().size([height - 40, width - 160]);
    const hierarchy = d3.hierarchy<TreeNode>(data, d => (!collapsed[d.job_id] ? d.children : undefined));
    const tree = layout(hierarchy);

    const g = svg.append('g').attr('transform', 'translate(80,20)');

    // Links
    g.selectAll('path.link')
      .data(tree.links())
      .enter()
      .append('path')
      .attr('class', 'link')
      .attr('fill', 'none')
      .attr('stroke', '#ccc')
      .attr('d', d3.linkHorizontal()
        .x((d: any) => d.y)
        .y((d: any) => d.x) as any);

    // Nodes
    const node = g.selectAll('g.node')
      .data(tree.descendants())
      .enter()
      .append('g')
      .attr('class', 'node')
      .attr('transform', (d: any) => `translate(${d.y},${d.x})`)
      .style('cursor', 'pointer')
      .on('click', (_e, d: any) => {
        const id = d.data.job_id as string;
        setCollapsed(prev => ({ ...prev, [id]: !prev[id] }));
      });

    node.append('circle')
      .attr('r', 6)
      .attr('fill', (d: any) => STATUS_COLOR[d.data.status] || '#9aa0a6');

    node.append('text')
      .attr('dx', 10)
      .attr('dy', 4)
      .style('font', '12px sans-serif')
      .text((d: any) => `${d.data.job_id.slice(0, 6)} • d${d.data.depth} • ${d.data.status}`);
  }, [data, width, height, collapsed]);

  return (
    <svg ref={svgRef} role="img" aria-label="Hierarchy visualization" width={width} height={height} />
  );
};

export default HierarchyVisualization;

