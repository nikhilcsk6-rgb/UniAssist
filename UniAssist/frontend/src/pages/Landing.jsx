import { Link } from 'react-router-dom'

const FEATURES = [
  ['💬', 'AI University Chatbot', 'Answers about admissions, fees, exams and policies from official documents, with page-level citations.'],
  ['📄', 'Document Assistant', 'Summaries, key points, topic explanations and study notes from your own PDFs, DOCX and TXT files.'],
  ['📝', 'Question Paper Generator', 'MCQ, short, long and true/false questions with answer keys and PDF export.'],
  ['🎓', 'Study Assistant', 'Study plans, flashcards, quizzes and revision notes in English, Kannada and Hindi.'],
  ['🛡️', 'Grounded & Safe', 'Retrieval-Augmented Generation with hallucination safeguards and prompt-injection protection.'],
  ['📊', 'Research Module', 'Measured comparison of an LLM with and without RAG on your own benchmark.'],
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-navy-900 via-navy-800 to-navy-950 text-white">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5">
        <div className="flex items-center gap-2 text-xl font-bold">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600" aria-hidden="true">U</span>UniAssist
        </div>
        <nav className="flex gap-2" aria-label="Account">
          <Link to="/login" className="btn btn-ghost">Log in</Link>
          <Link to="/register" className="btn btn-primary">Get started</Link>
        </nav>
      </header>
      <main>
        <section className="mx-auto max-w-4xl px-5 py-16 text-center animate-fadeUp">
          <span className="badge bg-brand-600/30 text-brand-200">Generative AI · LLM · RAG</span>
          <h1 className="mt-4 text-4xl font-extrabold leading-tight md:text-6xl">Your intelligent <span className="text-brand-400">university assistant</span></h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-navy-100">Ask questions about your university, understand study material, generate exam papers and learn in your language, with answers grounded in official documents.</p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link to="/register" className="btn btn-primary !px-6 !py-3">Create an account</Link>
            <Link to="/login" className="btn btn-ghost !px-6 !py-3">Try a demo account</Link>
          </div>
        </section>
        <section className="mx-auto grid max-w-6xl gap-4 px-5 pb-20 sm:grid-cols-2 lg:grid-cols-3" aria-label="Features">
          {FEATURES.map(([icon, t, d]) => (
            <div key={t} className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur">
              <div className="text-3xl" aria-hidden="true">{icon}</div>
              <h2 className="mt-2 text-lg font-semibold">{t}</h2>
              <p className="mt-1 text-sm text-navy-100">{d}</p>
            </div>
          ))}
        </section>
      </main>
      <footer className="border-t border-white/10 py-6 text-center text-xs text-navy-200">UniAssist · MCA academic project</footer>
    </div>
  )
}
