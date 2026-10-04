import { ApiError } from "./client";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

function extractFilename(contentDisposition: string | null, fallback: string): string {
  if (!contentDisposition) return fallback;
  const match = /filename="([^"]+)"/.exec(contentDisposition);
  return match ? match[1] : fallback;
}

async function downloadFromUrl(url: string, fallbackFilename: string): Promise<void> {
  const response = await fetch(url, { credentials: "include" });

  if (!response.ok) {
    let detail = "Failed to generate this report.";
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // no JSON body
    }
    throw new ApiError(response.status, detail);
  }

  const blob = await response.blob();
  const filename = extractFilename(response.headers.get("content-disposition"), fallbackFilename);

  // Trigger a real browser download via a temporary, invisible link —
  // the standard way to save a fetched blob without navigating away.
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(objectUrl);
}

export type ReportFormat = "pdf" | "markdown";

export const reportsApi = {
  downloadLabReport: (labId: string, format: ReportFormat) =>
    downloadFromUrl(`${API_BASE_URL}/labs/${labId}/report?format=${format}`, `lab-report.${format === "pdf" ? "pdf" : "md"}`),
  downloadLearningSummary: (format: ReportFormat) =>
    downloadFromUrl(
      `${API_BASE_URL}/reports/learning-summary?format=${format}`,
      `learning-summary.${format === "pdf" ? "pdf" : "md"}`
    ),
};
