import SignalBars from "./SignalBars";

const VERDICT_COLOR = {
  ai: "var(--red)",
  uncertain: "var(--amber)",
  human: "var(--green)",
};

const VERDICT_DIM = {
  ai: "rgba(239,68,68,0.08)",
  uncertain: "rgba(245,158,11,0.08)",
  human: "rgba(34,197,94,0.08)",
};

const VERDICT_LABEL = {
  ai: "AI GENERATED",
  uncertain: "UNCERTAIN",
  human: "LIKELY HUMAN",
};

const CONFIDENCE_COLOR = {
  high: "var(--red)",
  medium: "var(--amber)",
  low: "var(--muted)",
};

export default function OverallScore({ overall, onReset }) {
  if (!overall) return null;

  const {
    overall_score,
    ml_score,
    signal_score,
    overall_verdict,
    confidence,
    verdict_reasoning,
    frame_count,
    ai_frame_count,
    uncertain_frame_count,
    human_frame_count,
    mean_signals,
    score_timeline,
  } = overall;

  const color = VERDICT_COLOR[overall_verdict] || "var(--muted)";
  const dim = VERDICT_DIM[overall_verdict] || "transparent";
  const confColor = CONFIDENCE_COLOR[confidence] || "var(--muted)";

  return (
    <div
      style={{
        padding: "40px 24px 32px",
        maxWidth: "960px",
        margin: "0 auto",
      }}
    >
      {/* Main verdict card */}
      <div
        style={{
          background: "var(--card)",
          border: `1px solid ${color}`,
          borderRadius: "16px",
          padding: "32px",
          marginBottom: "24px",
          display: "flex",
          flexDirection: "column",
          gap: "24px",
        }}
      >
        {/* Verdict + score */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <p
              style={{
                fontFamily: "var(--mono)",
                fontSize: "11px",
                color: "var(--muted)",
                textTransform: "uppercase",
                letterSpacing: "2px",
                marginBottom: "8px",
              }}
            >
              OVERALL VERDICT
            </p>
            <h2
              style={{
                fontFamily: "var(--display)",
                fontSize: "32px",
                fontWeight: 700,
                color: color,
                marginBottom: "8px",
              }}
            >
              {VERDICT_LABEL[overall_verdict] || overall_verdict.toUpperCase()}
            </h2>
            {confidence && (
              <span
                style={{
                  fontFamily: "var(--mono)",
                  fontSize: "11px",
                  textTransform: "uppercase",
                  letterSpacing: "0.5px",
                  color: confColor,
                  border: `1px solid ${confColor}`,
                  borderRadius: "100px",
                  padding: "3px 10px",
                }}
              >
                {confidence} confidence
              </span>
            )}
          </div>
          <div style={{ textAlign: "right" }}>
            <p
              style={{
                fontFamily: "var(--mono)",
                fontSize: "64px",
                fontWeight: 700,
                color: color,
                lineHeight: 1,
              }}
            >
              {Math.round(overall_score * 100)}%
            </p>
            <p
              style={{
                fontFamily: "var(--mono)",
                fontSize: "11px",
                color: "var(--muted)",
                marginTop: "4px",
              }}
            >
              AI PROBABILITY
            </p>
          </div>
        </div>

        {/* Score breakdown: ML vs Signal */}
        {(ml_score !== undefined || signal_score !== undefined) && (
          <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
            <ScoreChip
              label="ML MODEL"
              value={ml_score}
              color={ml_score >= 0.55 ? "var(--red)" : ml_score >= 0.30 ? "var(--amber)" : "var(--green)"}
            />
            <ScoreChip
              label="SIGNAL SCORE"
              value={signal_score}
              color={signal_score >= 0.55 ? "var(--red)" : signal_score >= 0.30 ? "var(--amber)" : "var(--green)"}
            />
          </div>
        )}

        {/* Frame breakdown */}
        <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
          <StatPill label="TOTAL" value={frame_count} color="var(--text)" />
          <StatPill label="AI" value={ai_frame_count} color="var(--red)" />
          <StatPill label="UNCERTAIN" value={uncertain_frame_count} color="var(--amber)" />
          <StatPill label="HUMAN" value={human_frame_count} color="var(--green)" />
        </div>

        {/* Verdict reasoning */}
        {verdict_reasoning && (
          <div
            style={{
              background: "var(--bg2)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              padding: "12px 14px",
            }}
          >
            <p
              style={{
                fontFamily: "var(--mono)",
                fontSize: "9px",
                textTransform: "uppercase",
                color: "var(--muted)",
                letterSpacing: "1px",
                marginBottom: "6px",
              }}
            >
              DETECTION REASONING
            </p>
            <p
              style={{
                fontFamily: "var(--mono)",
                fontSize: "11px",
                color: "var(--text)",
                lineHeight: 1.6,
              }}
            >
              {verdict_reasoning}
            </p>
          </div>
        )}

        {/* Score timeline */}
        {score_timeline && score_timeline.length > 0 && (
          <div>
            <p
              style={{
                fontFamily: "var(--mono)",
                fontSize: "9px",
                textTransform: "uppercase",
                color: "var(--muted)",
                letterSpacing: "1px",
                marginBottom: "8px",
              }}
            >
              SCORE TIMELINE
            </p>
            <div style={{ display: "flex", alignItems: "flex-end", gap: "2px", height: "48px" }}>
              {score_timeline.map((s, i) => (
                <div
                  key={i}
                  title={`Frame ${i}: ${Math.round(s * 100)}%`}
                  style={{
                    flex: 1,
                    height: `${Math.round(s * 100)}%`,
                    minHeight: "2px",
                    background:
                      s >= 0.55 ? "var(--red)"
                        : s >= 0.30 ? "var(--amber)"
                        : "var(--green)",
                    borderRadius: "2px 2px 0 0",
                    transition: "height 0.5s ease",
                  }}
                />
              ))}
            </div>
          </div>
        )}

        {/* Mean signals */}
        {mean_signals && (
          <div>
            <p
              style={{
                fontFamily: "var(--mono)",
                fontSize: "9px",
                textTransform: "uppercase",
                color: "var(--muted)",
                letterSpacing: "1px",
                marginBottom: "10px",
              }}
            >
              MEAN FORENSIC SIGNALS
            </p>
            <SignalBars signals={mean_signals} />
          </div>
        )}
      </div>

      {/* Reset button */}
      <button
        onClick={onReset}
        style={{
          background: "transparent",
          border: "1px solid var(--border)",
          borderRadius: "8px",
          color: "var(--muted)",
          fontFamily: "var(--mono)",
          fontSize: "12px",
          textTransform: "uppercase",
          letterSpacing: "1px",
          padding: "10px 20px",
          cursor: "pointer",
          transition: "border-color 0.2s, color 0.2s",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = "var(--border-hi)";
          e.currentTarget.style.color = "var(--text)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = "var(--border)";
          e.currentTarget.style.color = "var(--muted)";
        }}
      >
        ← ANALYZE ANOTHER VIDEO
      </button>
    </div>
  );
}

function StatPill({ label, value, color }) {
  return (
    <div
      style={{
        background: "var(--bg2)",
        border: "1px solid var(--border)",
        borderRadius: "8px",
        padding: "8px 16px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "2px",
      }}
    >
      <span
        style={{
          fontFamily: "var(--mono)",
          fontSize: "22px",
          fontWeight: 700,
          color: color,
        }}
      >
        {value}
      </span>
      <span
        style={{
          fontFamily: "var(--mono)",
          fontSize: "9px",
          color: "var(--muted)",
          textTransform: "uppercase",
          letterSpacing: "1px",
        }}
      >
        {label}
      </span>
    </div>
  );
}

function ScoreChip({ label, value, color }) {
  if (value === undefined || value === null) return null;
  return (
    <div
      style={{
        background: "var(--bg2)",
        border: `1px solid ${color}`,
        borderRadius: "8px",
        padding: "6px 14px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "2px",
        minWidth: "90px",
      }}
    >
      <span
        style={{
          fontFamily: "var(--mono)",
          fontSize: "18px",
          fontWeight: 700,
          color: color,
        }}
      >
        {Math.round(value * 100)}%
      </span>
      <span
        style={{
          fontFamily: "var(--mono)",
          fontSize: "9px",
          color: "var(--muted)",
          textTransform: "uppercase",
          letterSpacing: "1px",
        }}
      >
        {label}
      </span>
    </div>
  );
}
