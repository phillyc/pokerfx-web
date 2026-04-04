export default function FeatureGrid() {
  return (
    <section className="py-24 max-w-7xl mx-auto px-6" id="features">
      <div className="mb-16 text-center lg:text-left">
        <h2 className="text-4xl md:text-5xl font-headline font-bold mb-4 tracking-tight">
          Precision <span className="text-primary-container">Automated</span>
        </h2>
        <p className="text-on-surface-variant max-w-2xl">
          Stop spending hours in Premiere. Let our neural engine handle the grunt work while you focus on the strategy.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Main Card — Zoom & Crop (wide) */}
        <div className="md:col-span-2 group relative overflow-hidden rounded-3xl bg-surface-container-low p-8 border border-outline-variant/10 hover:border-primary-container/30 transition-all duration-300">
          <div className="relative z-10">
            {/* center_focus_strong icon */}
            <svg className="w-10 h-10 text-primary-container mb-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
              <path d="M3 7V5a2 2 0 012-2h2M17 3h2a2 2 0 012 2v2M21 17v2a2 2 0 01-2 2h-2M7 21H5a2 2 0 01-2-2v-2" strokeLinecap="round" />
              <circle cx="12" cy="12" r="3" />
            </svg>
            <h3 className="text-3xl font-headline font-bold text-white mb-4">
              Automated Zoom & Crop
            </h3>
            <p className="text-on-surface-variant max-w-sm mb-8">
              Our AI tracks the action, automatically framing every street and all-in moment for maximum viewer engagement.
            </p>
            <div className="flex gap-4">
              <span className="px-4 py-2 bg-surface-container-high rounded-xl text-sm font-headline font-bold text-white border border-white/5">Dynamic Tracking</span>
              <span className="px-4 py-2 bg-surface-container-high rounded-xl text-sm font-headline font-bold text-white border border-white/5">4K Intelligent Upscale</span>
            </div>
          </div>
          {/* Decorative gradient overlay */}
          <div className="absolute right-0 bottom-0 w-1/2 h-full bg-gradient-to-l from-primary-container/10 to-transparent opacity-20 group-hover:opacity-40 transition-opacity duration-300" />
        </div>

        {/* AI Face Blurring */}
        <div className="bg-surface-container p-8 rounded-3xl border border-outline-variant/10 flex flex-col justify-between">
          <div>
            {/* face_retouching_off icon */}
            <svg className="w-10 h-10 text-secondary-container mb-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
              <circle cx="12" cy="10" r="7" />
              <path d="M8 14s1.5 2 4 2 4-2 4-2" strokeLinecap="round" />
              <path d="M9 9l6 6M15 9l-6 6" strokeLinecap="round" />
              <path d="M3 3l18 18" strokeLinecap="round" />
            </svg>
            <h3 className="text-2xl font-headline font-bold text-white mb-4">AI Face Blurring</h3>
            <p className="text-on-surface-variant text-sm">
              Protect player privacy automatically. Detected faces are seamlessly blurred with professional-grade overlays.
            </p>
          </div>
          <div className="mt-8 pt-8 border-t border-outline-variant/10">
            <span className="text-xs font-label text-secondary-container uppercase tracking-widest">Privacy Compliant</span>
          </div>
        </div>

        {/* Hole Card Detection */}
        <div className="bg-surface-container-lowest p-8 rounded-3xl border border-outline-variant/10 hover:bg-surface-container-low transition-colors group">
          {/* view_agenda icon */}
          <svg className="w-10 h-10 text-primary-container mb-6 group-hover:scale-110 transition-transform" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
            <rect x="3" y="3" width="7" height="9" rx="1" />
            <rect x="14" y="3" width="7" height="5" rx="1" />
            <rect x="14" y="12" width="7" height="9" rx="1" />
            <rect x="3" y="16" width="7" height="5" rx="1" />
          </svg>
          <h3 className="text-xl font-headline font-bold text-white mb-2">Hole Card Detection</h3>
          <p className="text-on-surface-variant text-sm">
            Real-time OCR recognizes every card dealt and auto-labels your hand history for the timeline.
          </p>
        </div>

        {/* Mass File Renaming */}
        <div className="bg-surface-container-lowest p-8 rounded-3xl border border-outline-variant/10 hover:bg-surface-container-low transition-colors group">
          {/* drive_file_rename_outline icon */}
          <svg className="w-10 h-10 text-primary-container mb-6 group-hover:scale-110 transition-transform" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
            <path d="M12 20h9" strokeLinecap="round" />
            <path d="M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4 12.5-12.5z" strokeLinejoin="round" />
          </svg>
          <h3 className="text-xl font-headline font-bold text-white mb-2">Mass File Renaming</h3>
          <p className="text-on-surface-variant text-sm">
            Organize terabytes of footage by date, stakes, and hand result with a single click.
          </p>
        </div>

        {/* Branded Animations */}
        <div className="md:col-span-3 lg:col-span-1 bg-gradient-to-br from-surface-container-low to-surface-container-high p-8 rounded-3xl border border-outline-variant/15 relative overflow-hidden">
          <div className="relative z-10">
            {/* animation icon */}
            <svg className="w-10 h-10 text-primary-container mb-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
              <rect x="2" y="2" width="20" height="20" rx="2" />
              <circle cx="8" cy="8" r="2" />
              <circle cx="16" cy="8" r="2" />
              <circle cx="8" cy="16" r="2" />
              <circle cx="16" cy="16" r="2" />
            </svg>
            <h3 className="text-2xl font-headline font-bold text-white mb-4">Branded Animations</h3>
            <p className="text-on-surface-variant text-sm mb-6">
              Custom transitions and animated hole card overlays that sync with your hand strength.
            </p>
            <a href="#" className="text-primary-container font-headline font-bold flex items-center gap-2 group/link">
              Explore Assets
              <svg className="w-4 h-4 group-hover/link:translate-x-1 transition-transform" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <path d="M5 12h14M12 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
