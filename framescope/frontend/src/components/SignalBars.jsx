const SIGNAL_LABELS = {
  texture_uniformity: "TEXTURE",
  noise_level: "NOISE",
  frequency_artifact: "FREQUENCY",
  color_uniformity: "COLOR",
};

function barColor(value) {
  if (value >= 0.65) return "var(--red)";
  if (value >= 0.35) return "var(--amber)";
  return "var(--green)";
}

export default function SignalBars({ signals }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
      {Object.entries(SIGNAL_LABELS).map(([key, label]) => {
        const value = signals?.[key] ?? 0;
        return (
          <div key={key} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span
              style={{
                fontFamily: "var(--mono)",
                fontSize: "10px",
                color: "var(--muted)",
                width: "70px",
                flexShrink: 0,
              }}
            >
              {label}
            </span>
            <div
              style={{
                flex: 1,
                height: "3px",
                background: "var(--dim)",
                borderRadius: "2px",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  height: "100%",
                  width: `${Math.round(value * 100)}%`,
                  background: barColor(value),
                  borderRadius: "2px",
                  transition: "width 0.7s cubic-bezier(0.4,0,0.2,1)",
                }}
              />
            </div>
            <span
              style={{
                fontFamily: "var(--mono)",
                fontSize: "11px",
                color: "var(--text)",
                width: "32px",
                textAlign: "right",
                flexShrink: 0,
              }}
            >
              {Math.round(value * 100)}%
            </span>
          </div>
        );
      })}
    </div>
  );
}
