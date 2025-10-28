import React from 'react';

type Usage = {
  depth: number;
  used: number;
  quota: number;
  warn_80: boolean;
  warn_90: boolean;
};

type Props = {
  usageByDepth: Record<number, Usage>;
};

export const ResourceUsageChart: React.FC<Props> = ({ usageByDepth }) => {
  const entries = Object.values(usageByDepth).sort((a, b) => a.depth - b.depth);
  return (
    <div role="region" aria-label="Resource usage by depth" style={{ display: 'flex', gap: 12 }}>
      {entries.map(u => {
        const pct = u.quota ? (u.used / u.quota) : 0;
        const color = u.warn_90 ? '#ea4335' : (u.warn_80 ? '#fbbc05' : '#34a853');
        return (
          <div key={u.depth} style={{ minWidth: 120 }}>
            <div style={{ marginBottom: 4 }}>Depth {u.depth}</div>
            <div
              style={{
                height: 120,
                width: 24,
                border: '1px solid #ccc',
                position: 'relative',
                background: '#f1f3f4',
              }}
            >
              <div
                role="progressbar"
                aria-valuemin={0}
                aria-valuemax={u.quota}
                aria-valuenow={u.used}
                title={`${u.used}/${u.quota}`}
                style={{
                  position: 'absolute',
                  bottom: 0,
                  width: '100%',
                  height: `${Math.min(100, Math.round(pct * 100))}%`,
                  background: color,
                }}
              />
            </div>
            <div style={{ fontSize: 12, color: '#5f6368', marginTop: 4 }}>{u.used}/{u.quota}</div>
          </div>
        );
      })}
    </div>
  );
};

export default ResourceUsageChart;

