export type EvidenceType =
  | "screenshot"
  | "image"
  | "log"
  | "pcap"
  | "text"
  | "detection_rule"
  | "configuration"
  | "report";

export const EVIDENCE_TYPE_LABELS: Record<EvidenceType, string> = {
  screenshot: "Screenshot",
  image: "Image",
  log: "Log file",
  pcap: "PCAP",
  text: "Text file",
  detection_rule: "Detection rule",
  configuration: "Configuration",
  report: "Report",
};

export interface Evidence {
  id: string;
  lab_id: string;
  finding_id: string | null;
  evidence_type: EvidenceType;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  sha256_hash: string;
  description: string | null;
  notes: string | null;
  is_public: boolean;
  uploaded_at: string;
}

export interface EvidenceWithLab extends Evidence {
  lab_title: string;
}

export interface Finding {
  id: string;
  lab_id: string;
  title: string;
  description: string | null;
  severity: "Info" | "Low" | "Medium" | "High" | null;
  created_at: string;
}

export interface EvidenceUpdatePayload {
  description?: string;
  notes?: string;
  is_public?: boolean;
  finding_id?: string;
}
