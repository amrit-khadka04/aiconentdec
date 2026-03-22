import { useState, useEffect, useRef } from "react";
import { api } from "./api";
import UploadZone from "./components/UploadZone";
import ProgressBar from "./components/ProgressBar";
import OverallScore from "./components/OverallScore";
import FrameGrid from "./components/FrameGrid";

const POLL_INTERVAL_MS = 1500;

export default function App() {
  const [jobId, setJobId] = useState(null);
  const [jobData, setJobData] = useState(null);
  const intervalRef = useRef(null);

  const handleJobStarted = (id) => {
    setJobId(id);
    setJobData(null);
  };

  useEffect(() => {
    if (!jobId) return;

    const poll = async () => {
      try {
        const data = await api.getJob(jobId);
        setJobData(data);
        if (data.status === "complete" || data.status === "error") {
          clearInterval(intervalRef.current);
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    };

    poll();
    intervalRef.current = setInterval(poll, POLL_INTERVAL_MS);

    return () => clearInterval(intervalRef.current);
  }, [jobId]);

  const handleReset = () => {
    setJobId(null);
    setJobData(null);
  };

  // Idle state
  if (!jobId) {
    return <UploadZone onJobStarted={handleJobStarted} />;
  }

  // Processing / complete / error
  const status = jobData?.status || "processing";
  const completedFrames = jobData?.completed_frames || 0;
  const totalFrames = jobData?.total_frames || 0;
  const results = jobData?.results || [];
  const overall = jobData?.overall || null;
  const topSuspicious = overall?.top_suspicious_frames || [];

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      {/* Header */}
      <div
        style={{
          padding: "20px 24px",
          borderBottom: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <h1
          style={{
            fontFamily: "var(--display)",
            fontSize: "22px",
            fontWeight: 700,
            cursor: "pointer",
          }}
          onClick={handleReset}
        >
          Frame<span style={{ color: "var(--blue)" }}>Scope</span>
        </h1>
        {status === "processing" && (
          <span
            style={{
              fontFamily: "var(--mono)",
              fontSize: "11px",
              color: "var(--amber)",
              textTransform: "uppercase",
              letterSpacing: "1px",
            }}
          >
            ● PROCESSING
          </span>
        )}
        {status === "complete" && (
          <span
            style={{
              fontFamily: "var(--mono)",
              fontSize: "11px",
              color: "var(--green)",
              textTransform: "uppercase",
              letterSpacing: "1px",
            }}
          >
            ✓ COMPLETE
          </span>
        )}
        {status === "error" && (
          <span
            style={{
              fontFamily: "var(--mono)",
              fontSize: "11px",
              color: "var(--red)",
              textTransform: "uppercase",
              letterSpacing: "1px",
            }}
          >
            ✗ ERROR
          </span>
        )}
      </div>

      {/* Progress */}
      {status === "processing" && (
        <ProgressBar
          status={status}
          completedFrames={completedFrames}
          totalFrames={totalFrames}
        />
      )}

      {/* Error */}
      {status === "error" && (
        <div style={{ padding: "48px 24px", textAlign: "center" }}>
          <p
            style={{
              fontFamily: "var(--mono)",
              fontSize: "14px",
              color: "var(--red)",
              marginBottom: "16px",
            }}
          >
            Analysis failed: {jobData?.error || "Unknown error"}
          </p>
          <button
            onClick={handleReset}
            style={{
              background: "var(--dim)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              color: "var(--text)",
              fontFamily: "var(--mono)",
              fontSize: "12px",
              padding: "10px 20px",
              cursor: "pointer",
              textTransform: "uppercase",
              letterSpacing: "1px",
            }}
          >
            ← TRY AGAIN
          </button>
        </div>
      )}

      {/* Results */}
      {status === "complete" && overall && (
        <>
          <OverallScore overall={overall} onReset={handleReset} />
          <FrameGrid results={results} topSuspiciousFrames={topSuspicious} />
        </>
      )}

      {/* Live frame grid during processing */}
      {status === "processing" && results.length > 0 && (
        <FrameGrid results={results} topSuspiciousFrames={[]} />
      )}
    </div>
  );
}
