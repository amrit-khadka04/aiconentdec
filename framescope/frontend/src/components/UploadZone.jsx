import { useRef, useState } from "react";
import { api } from "../api";

const FilmIcon = () => (
  <svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="4" y="12" width="56" height="40" rx="4" stroke="var(--muted)" strokeWidth="2" fill="none" />
    <rect x="4" y="12" width="10" height="40" fill="var(--dim)" stroke="var(--muted)" strokeWidth="2" />
    <rect x="50" y="12" width="10" height="40" fill="var(--dim)" stroke="var(--muted)" strokeWidth="2" />
    {[16, 24, 32, 40].map((y) => (
      <rect key={y} x="6" y={y} width="6" height="6" rx="1" fill="var(--muted)" />
    ))}
    {[16, 24, 32, 40].map((y) => (
      <rect key={y + 100} x="52" y={y} width="6" height="6" rx="1" fill="var(--muted)" />
    ))}
  </svg>
);

export default function UploadZone({ onJobStarted }) {
  const [dragOver, setDragOver] = useState(false);
  const [file, setFile] = useState(null);
  const [sampleRate, setSampleRate] = useState(30);
  const [maxFrames, setMaxFrames] = useState(40);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef();

  const handleFile = (f) => {
    setFile(f);
    setError(null);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("sample_rate", sampleRate);
      fd.append("max_frames", maxFrames);
      const { data } = await api.detect(fd);
      onJobStarted(data.job_id);
    } catch (err) {
      setError(err?.response?.data?.detail || "Upload failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const formatSize = (bytes) => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
      }}
    >
      <div style={{ width: "100%", maxWidth: "540px" }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "32px" }}>
          <h1
            style={{
              fontFamily: "var(--display)",
              fontSize: "36px",
              fontWeight: 700,
              letterSpacing: "-0.5px",
              marginBottom: "8px",
            }}
          >
            Frame<span style={{ color: "var(--blue)" }}>Scope</span>
          </h1>
          <p style={{ fontFamily: "var(--mono)", fontSize: "12px", color: "var(--muted)" }}>
            AI-GENERATED VIDEO DETECTION
          </p>
        </div>

        {/* Drop zone */}
        <div
          onClick={() => !loading && inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          style={{
            border: `2px dashed ${dragOver ? "var(--blue)" : file ? "var(--border-hi)" : "var(--border)"}`,
            borderRadius: "16px",
            minHeight: "300px",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: "16px",
            cursor: loading ? "default" : "pointer",
            background: dragOver ? "rgba(59,130,246,0.05)" : "var(--card)",
            transition: "border-color 0.2s, background 0.2s",
            padding: "40px 24px",
          }}
        >
          <FilmIcon />
          {file ? (
            <div style={{ textAlign: "center" }}>
              <p style={{ fontFamily: "var(--mono)", fontSize: "13px", color: "var(--text)", marginBottom: "4px" }}>
                {file.name}
              </p>
              <p style={{ fontFamily: "var(--mono)", fontSize: "11px", color: "var(--muted)" }}>
                {formatSize(file.size)}
              </p>
            </div>
          ) : (
            <div style={{ textAlign: "center" }}>
              <p style={{ fontFamily: "var(--display)", fontSize: "28px", fontWeight: 600, marginBottom: "8px" }}>
                Drop your video
              </p>
              <p style={{ fontFamily: "var(--mono)", fontSize: "13px", color: "var(--muted)" }}>
                MP4 · MOV · AVI · WEBM
              </p>
            </div>
          )}
          <input
            ref={inputRef}
            type="file"
            accept=".mp4,.mov,.avi,.webm,.mkv"
            style={{ display: "none" }}
            onChange={(e) => e.target.files[0] && handleFile(e.target.files[0])}
          />
        </div>

        {/* Sliders */}
        <div
          style={{
            marginTop: "24px",
            background: "var(--card)",
            borderRadius: "12px",
            border: "1px solid var(--border)",
            padding: "20px",
            display: "flex",
            flexDirection: "column",
            gap: "16px",
          }}
        >
          <SliderRow
            label="SAMPLE EVERY"
            unit="frames"
            value={sampleRate}
            min={5}
            max={60}
            onChange={setSampleRate}
          />
          <SliderRow
            label="UP TO"
            unit="frames total"
            value={maxFrames}
            min={10}
            max={60}
            onChange={setMaxFrames}
          />
        </div>

        {error && (
          <p
            style={{
              marginTop: "12px",
              fontFamily: "var(--mono)",
              fontSize: "12px",
              color: "var(--red)",
              textAlign: "center",
            }}
          >
            {error}
          </p>
        )}

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={!file || loading}
          style={{
            marginTop: "20px",
            width: "100%",
            padding: "14px",
            background: !file || loading ? "var(--dim)" : "var(--blue)",
            border: "none",
            borderRadius: "10px",
            color: "#fff",
            fontFamily: "var(--mono)",
            fontSize: "13px",
            fontWeight: 700,
            letterSpacing: "2px",
            textTransform: "uppercase",
            cursor: !file || loading ? "default" : "pointer",
            transition: "background 0.2s",
          }}
        >
          {loading ? "UPLOADING..." : "ANALYZE VIDEO"}
        </button>
      </div>
    </div>
  );
}

function SliderRow({ label, unit, value, min, max, onChange }) {
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
        <span style={{ fontFamily: "var(--mono)", fontSize: "11px", color: "var(--muted)" }}>
          {label}
        </span>
        <span style={{ fontFamily: "var(--mono)", fontSize: "11px", color: "var(--text)" }}>
          {value} {unit}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{ width: "100%", accentColor: "var(--blue)" }}
      />
    </div>
  );
}
