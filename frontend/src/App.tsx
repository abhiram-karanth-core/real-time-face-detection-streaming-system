import React, { useRef, useEffect, useState, useCallback } from "react";
import { ConnectionStatus, ROI, ROIResponse } from "./types";

const WS_URL = process.env.REACT_APP_WS_URL || "ws://localhost:8000/ws/stream";
const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// How often (ms) we capture a frame from the webcam and send it.
// 100ms = ~10fps — a good balance between smoothness and CPU load.
const CAPTURE_INTERVAL_MS = 100;

export default function App() {

  const webcamRef  = useRef<HTMLVideoElement>(null);
  const canvasRef  = useRef<HTMLCanvasElement>(null);
  const displayRef = useRef<HTMLImageElement>(null);

  const wsRef       = useRef<WebSocket | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const sessionRef  = useRef<string | null>(null);

  const [status, setStatus]       = useState<ConnectionStatus>("disconnected");
  const [roiHistory, setRoiHistory] = useState<ROI[]>([]);
  const [latestROI, setLatestROI]   = useState<ROI | null>(null);
  const [error, setError]           = useState<string | null>(null);


  const startWebcam = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: "user" },
        audio: false,
      });
      if (webcamRef.current) {
        webcamRef.current.srcObject = stream;
        await webcamRef.current.play();
      }
    } catch (err) {
      setError("Camera access denied. Please allow camera permissions.");
    }
  }, []);


  const connect = useCallback(() => {
    setStatus("connecting");
    setError(null);


    sessionRef.current = crypto.randomUUID();

    const ws = new WebSocket(`${WS_URL}?session_id=${sessionRef.current}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("connected");
      startSending();
    };

    ws.onmessage = (event: MessageEvent) => {
      if (displayRef.current) {
        displayRef.current.src = event.data as string;
      }
    };

    ws.onerror = () => {
      setStatus("error");
      setError("WebSocket connection failed.");
    };

    ws.onclose = () => {
      setStatus("disconnected");
      stopSending();
    };
  }, []);


  const startSending = useCallback(() => {
    intervalRef.current = setInterval(() => {
      const video  = webcamRef.current;
      const canvas = canvasRef.current;
      const ws     = wsRef.current;

      if (!video || !canvas || !ws || ws.readyState !== WebSocket.OPEN) return;

      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      canvas.width  = video.videoWidth;
      canvas.height = video.videoHeight;

      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);


      const dataUrl  = canvas.toDataURL("image/jpeg", 0.8);
      const base64   = dataUrl.split(",")[1];

      ws.send(base64);
    }, CAPTURE_INTERVAL_MS);
  }, []);

  const stopSending = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);


  const disconnect = useCallback(() => {
    stopSending();
    wsRef.current?.close();
  }, [stopSending]);


  const fetchROIHistory = useCallback(async () => {
    if (!sessionRef.current) return;
    try {
      const res: Response = await fetch(
        `${API_URL}/roi?session_id=${sessionRef.current}`
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: ROIResponse = await res.json();
      setRoiHistory(data.roi);
      setLatestROI(data.roi[data.roi.length - 1] ?? null);
    } catch (err) {
      console.error("Failed to fetch ROI history:", err);
    }
  }, []);


  useEffect(() => {
    startWebcam();
    return () => {
      disconnect();
      // Stop all webcam tracks to turn off the camera indicator light
      const stream = webcamRef.current?.srcObject as MediaStream | null;
      stream?.getTracks().forEach((t) => t.stop());
    };
  }, [startWebcam, disconnect]);


  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Real-Time Face Detection</h1>

      {}
      <div style={{ ...styles.badge, background: statusColor(status) }}>
        {status.toUpperCase()}
      </div>

      {error && <p style={styles.error}>{error}</p>}

      {}
      <div style={styles.feeds}>
        {}
        <canvas ref={canvasRef} style={styles.hidden} />

        {}
        <div style={styles.feed}>
          <p style={styles.label}>Your webcam</p>
          <video
            ref={webcamRef}
            muted
            playsInline
            autoPlay
            style={styles.video}
          />
        </div>

        {}
        <div style={styles.feed}>
          <p style={styles.label}>Annotated (backend)</p>
          <img
            ref={displayRef}
            alt="Annotated frame"
            style={styles.video}
          />
        </div>
      </div>

      {}
      <div style={styles.controls}>
        {status === "disconnected" || status === "error" ? (
          <button style={styles.btn} onClick={connect}>
            Start streaming
          </button>
        ) : (
          <button style={{ ...styles.btn, background: "#c0392b" }} onClick={disconnect}>
            Stop
          </button>
        )}
        <button style={{ ...styles.btn, background: "#2980b9" }} onClick={fetchROIHistory}>
          Fetch ROI history
        </button>
      </div>

      {}
      {latestROI && (
        <div style={styles.roiBox}>
          <strong>Latest detection</strong>
          <pre style={styles.pre}>{JSON.stringify(latestROI, null, 2)}</pre>
        </div>
      )}

      {}
      {roiHistory.length > 0 && (
        <div style={styles.table}>
          <h3>ROI history ({roiHistory.length} detections)</h3>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr>
                {["#", "x", "y", "w", "h", "confidence", "time"].map((h) => (
                  <th key={h} style={styles.th}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {roiHistory.map((r, i) => (
                <tr key={r.id}>
                  <td style={styles.td}>{i + 1}</td>
                  <td style={styles.td}>{r.x}</td>
                  <td style={styles.td}>{r.y}</td>
                  <td style={styles.td}>{r.width}</td>
                  <td style={styles.td}>{r.height}</td>
                  <td style={styles.td}>{r.confidence?.toFixed(2) ?? "—"}</td>
                  <td style={styles.td}>{new Date(r.detected_at).toLocaleTimeString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function statusColor(s: ConnectionStatus): string {
  return { connected: "#27ae60", connecting: "#f39c12", disconnected: "#7f8c8d", error: "#c0392b" }[s];
}

const styles: Record<string, React.CSSProperties> = {
  container: { maxWidth: 960, margin: "0 auto", padding: 24, fontFamily: "sans-serif" },
  title:     { fontSize: 24, marginBottom: 8 },
  badge:     { display: "inline-block", color: "#fff", borderRadius: 4, padding: "2px 10px", fontSize: 12, marginBottom: 12 },
  error:     { color: "#c0392b", margin: "8px 0" },
  feeds:     { display: "flex", gap: 16, flexWrap: "wrap" },
  feed:      { flex: 1, minWidth: 280 },
  label:     { margin: "0 0 4px", fontWeight: 600, fontSize: 13, color: "#555" },
  video:     { width: "100%", borderRadius: 6, background: "#000", minHeight: 240 },
  hidden:    { display: "none" },
  controls:  { display: "flex", gap: 10, margin: "16px 0" },
  btn:       { padding: "8px 18px", background: "#27ae60", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 14 },
  roiBox:    { background: "#f8f8f8", borderRadius: 6, padding: 12, marginBottom: 16 },
  pre:       { margin: 0, fontSize: 12 },
  table:     { overflowX: "auto" },
  th:        { background: "#eee", padding: "6px 10px", textAlign: "left", border: "1px solid #ddd" },
  td:        { padding: "4px 10px", border: "1px solid #eee" },
};