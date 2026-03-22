import { motion } from "framer-motion";
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

export default function FrameCard({ frameResult, isSuspicious }) {
  const {
    frame_index,
    timestamp_sec,
    ai_score,
    verdict,
    signals,
    base64_jpeg,
    reasons,
    primary_evidence,
    artifact_categories,
    confidence,
  } = frameResult;

  const color = VERDICT_COLOR[verdict] || "var(--muted)";
  const dim = VERDICT_DIM[verdict] || "transparent";
  const confColor = CONFIDENCE_COLOR[confidence] || "var(--muted)";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      style={{
        background: "var(--card)",
        border: `1px solid ${isSuspicious ? "var(--red)" : "var(--border)"}`,
        borderRadius: "12px",
        overflow: "hidden",
        transition: "transform 0.2s, border-color 0.2s",
        animation: isSuspicious ? "glowPulse 2s infinite" : "none",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = "translateY(-2px)";
        if (!isSuspicious)
          e.currentTarget.style.borderColor = "var(--border-hi)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = "translateY(0)";
        if (!isSuspicious)
          e.currentTarget.style.borderColor = "var(--border)";
      }}
    >
      {/* SECTION A: Image */}
      <div style={{ position: "relative" }}>
        <img
          src={`data:image/jpeg;base64,${base64_jpeg}`}
          alt={`Frame ${frame_index}`}
          style={{ width: "100%", display: "block" }}
        />
        {/* Top-left: frame index */}
        <span
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            fontFamily: "var(--mono)",
            fontSize: "11px",
            background: "rgba(0,0,0,0.7)",
            color: "var(--text)",
            padding: "3px 7px",
            borderRadius: "0 0 6px 0",
          }}
        >
          F{String(frame_index).padStart(3, "0")}
        </span>
        {/* Top-right: timestamp */}
        <span
          style={{
            position: "absolute",
            top: 0,
            right: 0,
            fontFamily: "var(--mono)",
            fontSize: "11px",
            background: "rgba(0,0,0,0.7)",
            color: "var(--text)",
            padding: "3px 7px",
            borderRadius: "0 0 0 6px",
          }}
        >
          {timestamp_sec.toFixed(1)}s
        </span>
        {/* Bottom center: TOP SUSPECT badge */}
        {isSuspicious && (
          <span
            style={{
              position: "absolute",
              bottom: 0,
              left: "50%",
              transform: "translateX(-50%)",
              fontFamily: "var(--mono)",
              fontSize: "10px",
              fontWeight: 700,
              textTransform: "uppercase",
              background: "rgba(239,68,68,0.85)",
              color: "#fff",
              padding: "4px 12px",
              borderRadius: "6px 6px 0 0",
              letterSpacing: "1px",
            }}
          >
            TOP SUSPECT
          </span>
        )}
      </div>

      {/* SECTION B: Score bar */}
      <div
        style={{
          height: "44px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 14px",
          background: dim,
          borderTop: `2px solid ${color}`,
        }}
      >
        <span
          style={{
            fontFamily: "var(--mono)",
            fontSize: "10px",
            fontWeight: 700,
            textTransform: "uppercase",
            border: `1px solid ${color}`,
            color: color,
            padding: "3px 10px",
            borderRadius: "100px",
            letterSpacing: "0.5px",
          }}
        >
          {VERDICT_LABEL[verdict] || verdict.toUpperCase()}
        </span>
        <span
          style={{
            fontFamily: "var(--mono)",
            fontSize: "26px",
            fontWeight: 700,
            color: color,
          }}
        >
          {Math.round(ai_score * 100)}%
        </span>
      </div>

      {/* SECTION C: Primary evidence + LLM analysis */}
      {(primary_evidence || (reasons && reasons.length > 0)) && (
        <div
          style={{
            padding: "12px 14px",
            borderTop: "1px solid var(--border)",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "8px",
            }}
          >
            <p
              style={{
                fontFamily: "var(--mono)",
                fontSize: "9px",
                textTransform: "uppercase",
                color: "var(--muted)",
                letterSpacing: "1px",
              }}
            >
              FORENSIC ANALYSIS
            </p>
            {confidence && (
              <span
                style={{
                  fontFamily: "var(--mono)",
                  fontSize: "9px",
                  textTransform: "uppercase",
                  letterSpacing: "0.5px",
                  color: confColor,
                  border: `1px solid ${confColor}`,
                  borderRadius: "100px",
                  padding: "2px 7px",
                }}
              >
                {confidence} confidence
              </span>
            )}
          </div>

          {/* Primary evidence */}
          {primary_evidence && (
            <p
              style={{
                fontFamily: "var(--mono)",
                fontSize: "11px",
                color: color,
                marginBottom: reasons && reasons.length > 0 ? "8px" : 0,
                lineHeight: 1.5,
              }}
            >
              ▶ {primary_evidence}
            </p>
          )}

          {/* Reason list */}
          {reasons && reasons.length > 0 && (
            <ul
              style={{
                margin: 0,
                padding: 0,
                listStyle: "none",
                display: "flex",
                flexDirection: "column",
                gap: "5px",
              }}
            >
              {reasons.map((r, i) => (
                <li
                  key={i}
                  style={{
                    fontFamily: "var(--mono)",
                    fontSize: "10px",
                    color: "var(--muted)",
                    lineHeight: 1.5,
                    paddingLeft: "12px",
                    position: "relative",
                  }}
                >
                  <span
                    style={{
                      position: "absolute",
                      left: 0,
                      color: "var(--border-hi)",
                    }}
                  >
                    ·
                  </span>
                  {r}
                </li>
              ))}
            </ul>
          )}

          {/* Artifact category tags */}
          {artifact_categories && artifact_categories.length > 0 && (
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: "4px",
                marginTop: "8px",
              }}
            >
              {artifact_categories.map((cat) => (
                <span
                  key={cat}
                  style={{
                    fontFamily: "var(--mono)",
                    fontSize: "9px",
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                    color: "var(--muted)",
                    border: "1px solid var(--border)",
                    borderRadius: "4px",
                    padding: "2px 6px",
                  }}
                >
                  {cat}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* SECTION D: Signals */}
      <div
        style={{
          padding: "12px 14px",
          borderTop: "1px solid var(--border)",
        }}
      >
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
          DETECTION SIGNALS
        </p>
        <SignalBars signals={signals} />
      </div>
    </motion.div>
  );
}
