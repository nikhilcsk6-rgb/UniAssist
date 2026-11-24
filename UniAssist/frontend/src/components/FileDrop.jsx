import { useRef, useState } from 'react'

// Drag-and-drop (or click / keyboard) file picker. Validation happens on the server too.
export default function FileDrop({ file, onFile, accept = '.pdf,.docx,.txt' }) {
  const input = useRef(null)
  const [over, setOver] = useState(false)
  const pick = (f) => f && onFile(f)
  return (
    <div
      role="button" tabIndex={0} aria-label="Choose or drop a file"
      onClick={() => input.current.click()}
      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && input.current.click()}
      onDragOver={(e) => { e.preventDefault(); setOver(true) }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => { e.preventDefault(); setOver(false); pick(e.dataTransfer.files[0]) }}
      className={`cursor-pointer rounded-xl border-2 border-dashed p-6 text-center transition ${over ? 'border-brand-500 bg-brand-50 dark:bg-navy-800' : 'border-slate-300 dark:border-navy-600'}`}
    >
      <input ref={input} type="file" accept={accept} className="hidden" onChange={(e) => pick(e.target.files[0])} />
      <div className="text-3xl" aria-hidden="true">📄</div>
      <p className="mt-1 text-sm font-medium">{file ? file.name : 'Drag & drop a PDF, DOCX or TXT file, or click to browse'}</p>
      {file && <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(0)} KB</p>}
    </div>
  )
}
