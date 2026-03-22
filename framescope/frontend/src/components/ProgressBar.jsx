export default function ProgressBar({ status, completedFrames, totalFrames }) {
  if (status === "complete" || status === "error") return null;

  const progress = totalFrames > 0 ? completedFrames / totalFrames : 0;

  return (
    <div
      style={{
        maxWidth: "600px",
        margin: "0 auto",
        padding: "48px 24px",
        textAlign: "center",
      }}
    >
      <p
        style={{
          fontFamily: "var(--display)",
          fontSize: "24px",
          fontWeight: 600,
          marginBottom: "8px",
        }}
      >
        Analyzing frames...
      </p>
      <p
        style={{
          fontFamily: "var(--mono)",
          fontSize: "13px",
          color: "var(--muted)",
          marginBottom: "24px",
        }}
      >
        Frame {completedFrames} of {totalFrames || "?"}
      </p>
      <div
        style={{
          height: "3px",
          background: "var(--dim)",
          borderRadius: "2px",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${Math.round(progress * 100)}%`,
            background: "var(--blue)",
            borderRadius: "2px",
            transition: "width 0.4s ease",
          }}
        />
      </div>
      <p
        style={{
          marginTop: "10px",
          fontFamily: "var(--mono)",
          fontSize: "11px",
          color: "var(--muted)",
        }}
      >
        {Math.round(progress * 100)}%
      </p>
    </div>
  );
}
