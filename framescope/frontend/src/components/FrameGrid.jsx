import FrameCard from "./FrameCard";

export default function FrameGrid({ results, topSuspiciousFrames }) {
  if (!results || results.length === 0) return null;

  const suspiciousSet = new Set(topSuspiciousFrames || []);

  const sorted = [...results].sort((a, b) => a.frame_index - b.frame_index);

  return (
    <div style={{ padding: "0 24px 48px" }}>
      <h2
        style={{
          fontFamily: "var(--display)",
          fontSize: "20px",
          fontWeight: 600,
          marginBottom: "20px",
          color: "var(--text)",
        }}
      >
        Frame Analysis
        <span
          style={{
            fontFamily: "var(--mono)",
            fontSize: "12px",
            color: "var(--muted)",
            marginLeft: "12px",
            fontWeight: 400,
          }}
        >
          {results.length} frames
        </span>
      </h2>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
          gap: "16px",
        }}
      >
        {sorted.map((frame) => (
          <FrameCard
            key={frame.frame_index}
            frameResult={frame}
            isSuspicious={suspiciousSet.has(frame.frame_index)}
          />
        ))}
      </div>
    </div>
  );
}
