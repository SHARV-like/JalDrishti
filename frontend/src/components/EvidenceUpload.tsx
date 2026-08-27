import { useEffect, useRef, useState } from "react";

export type EvidenceResult = { metadata: { gps: { latitude: number; longitude: number } | null; captured_at: string | null; orientation: number | null; image_format: string }; review_message: string | null; original_filename: string | null };

type EvidenceUploadProps = { onEvidenceUploaded: (result: EvidenceResult | null) => void };
const MAX_FILE_BYTES = 10 * 1024 * 1024;

export function EvidenceUpload({ onEvidenceUploaded }: EvidenceUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<EvidenceResult | null>(null);
  const [message, setMessage] = useState("Choose a JPEG or PNG under 10 MB. Files are inspected locally and are not stored.");

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);

  function inspectFile(file: File) {
    if (!["image/jpeg", "image/png"].includes(file.type)) { setMessage("Choose a JPEG or PNG image."); return; }
    if (file.size > MAX_FILE_BYTES) { setMessage("Image must be 10 MB or smaller."); return; }
    if (preview) URL.revokeObjectURL(preview);
    setPreview(URL.createObjectURL(file)); setProgress(0); setResult(null); onEvidenceUploaded(null); setMessage("Inspecting EXIF metadata…");
    const request = new XMLHttpRequest();
    request.open("POST", "http://localhost:8000/api/v1/field-evidence");
    request.upload.onprogress = (event) => { if (event.lengthComputable) setProgress(Math.round((event.loaded / event.total) * 100)); };
    request.onload = () => {
      if (request.status >= 200 && request.status < 300) { const evidence = JSON.parse(request.responseText) as EvidenceResult; setResult(evidence); onEvidenceUploaded(evidence); setProgress(100); setMessage(evidence.review_message ?? "GPS metadata found and shown on the map."); }
      else { const error = JSON.parse(request.responseText) as { detail?: { message?: string } }; setMessage(error.detail?.message ?? "Could not inspect this image."); setProgress(0); }
    };
    request.onerror = () => { setMessage("Could not reach the local API. Start the FastAPI service and try again."); setProgress(0); };
    const form = new FormData(); form.append("file", file); request.send(form);
  }

  return <section className="evidence-section" aria-labelledby="evidence-title"><div className="evidence-heading"><div><p className="eyebrow">FIELD EVIDENCE</p><h2 id="evidence-title">Upload Field Evidence</h2><p>Inspect a geo-tagged image to place an evidence marker in the demo watershed.</p></div><span className="local-chip">LOCAL ONLY</span></div><div className="evidence-grid"><button className="drop-zone" type="button" onClick={() => inputRef.current?.click()} onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); const file = event.dataTransfer.files[0]; if (file) inspectFile(file); }}><input ref={inputRef} type="file" accept="image/jpeg,image/png" onChange={(event) => { const file = event.target.files?.[0]; if (file) inspectFile(file); }} /><span className="upload-icon">↑</span><strong>Drop an image here or browse</strong><small>JPEG or PNG · 10 MB maximum</small></button>{preview ? <img className="evidence-preview" src={preview} alt="Selected field evidence preview" /> : <div className="preview-placeholder">Image preview will appear here</div>}</div><div className="upload-status"><div><span style={{ width: `${progress}%` }} /></div><p>{message}</p></div>{result ? <article className="evidence-card"><div><p className="eyebrow">EXTRACTED METADATA</p><h3>{result.original_filename}</h3></div><dl><div><dt>GPS location</dt><dd>{result.metadata.gps ? `${result.metadata.gps.latitude.toFixed(6)}, ${result.metadata.gps.longitude.toFixed(6)}` : "Not available"}</dd></div><div><dt>Capture time</dt><dd>{result.metadata.captured_at ?? "Not available"}</dd></div><div><dt>Orientation</dt><dd>{result.metadata.orientation ?? "Not available"}</dd></div></dl></article> : null}</section>;
}
