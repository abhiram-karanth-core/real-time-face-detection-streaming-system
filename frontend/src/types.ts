export interface ROI {
  id: number;
  session_id: string;
  frame_id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  confidence: number | null;
  detected_at: string;
}

export interface ROIResponse {
  session_id: string;
  count: number;
  roi: ROI[];
}

// WebSocket connection states
export type ConnectionStatus = "disconnected" | "connecting" | "connected" | "error";