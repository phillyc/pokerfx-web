export default function ComparisonSection() {
  const oldWayPainPoints = [
    {
      title: 'Hours of Manual Masking',
      desc: 'Tediously frame-by-frame blurring faces and hole cards.',
    },
    {
      title: 'Tedious Card Labeling',
      desc: 'Manually identifying and typing out every card for the UI.',
    },
    {
      title: 'Complex Keyframing',
      desc: 'Setting infinite keyframes just to track a chip stack movement.',
    },
  ];

  const pokerfxWayBenefits = [
    {
      title: 'Instant AI Detection',
      desc: 'Faces and sensitive info are detected and blurred in one pass.',
    },
    {
      title: 'Automated Overlays',
      desc: 'Broadcast-quality graphics sync automatically with detected cards.',
    },
    {
      title: 'One-Click Exports',
      desc: 'From raw session to viral-ready exports in under 5 minutes.',
    },
  ];

  return (
    <section className="py-24 bg-surface-container-lowest overflow-hidden">
      <div className="max-w-7xl mx-auto px-6">
        {/* Heading */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-headline font-bold mb-6 tracking-tight">
            The Manual Grind is{' '}
            <span className="text-secondary-container">Over</span>
          </h2>
          <p className="text-on-surface-variant max-w-2xl mx-auto text-lg">
            Stop sacrificing your session EV for hours behind a monitor. Compare the old way to the future of content.
          </p>
        </div>

        {/* Two Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative">
          {/* VS Divider */}
          <div className="hidden md:flex absolute inset-0 items-center justify-center pointer-events-none z-20">
            <div className="w-16 h-16 bg-background border border-outline-variant/30 rounded-full flex items-center justify-center font-headline font-bold text-xl text-primary-container shadow-[0_0_30px_rgba(42,229,0,0.2)]">
              VS
            </div>
          </div>

          {/* The Old Way */}
          <div className="bg-surface-container-low/40 rounded-[2rem] p-8 border border-white/5 relative group">
            <div className="flex items-center gap-4 mb-8">
              <div className="w-12 h-12 rounded-xl bg-surface-variant flex items-center justify-center">
                <svg className="w-6 h-6 text-gray-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                  <circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" />
                </svg>
              </div>
              <div>
                <h3 className="font-headline font-bold text-2xl text-white">The Old Way</h3>
                <p className="text-xs text-gray-500 font-label uppercase tracking-widest">Manual Editing</p>
              </div>
            </div>
            <ul className="space-y-6 mb-12">
              {oldWayPainPoints.map((item) => (
                <li key={item.title} className="flex items-start gap-4 opacity-70 group-hover:opacity-100 transition-opacity">
                  <svg className="w-5 h-5 text-error mt-1 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  <div>
                    <h4 className="text-white font-bold text-sm mb-1">{item.title}</h4>
                    <p className="text-sm text-on-surface-variant">{item.desc}</p>
                  </div>
                </li>
              ))}
            </ul>
            <div className="bg-surface-container rounded-2xl p-6 border border-white/5">
              <div className="text-3xl font-headline font-bold text-error mb-1">8+ Hours</div>
              <div className="text-xs font-label text-gray-500 uppercase tracking-widest">Per 10-Minute Vlog</div>
            </div>
          </div>

          {/* The PokerFX Way */}
          <div className="bg-primary-container/[0.03] rounded-[2rem] p-8 border border-primary-container/20 relative group overflow-hidden">
            <div className="absolute -top-24 -right-24 w-64 h-64 bg-primary-container/10 blur-[100px] rounded-full" />
            <div className="relative z-10">
              <div className="flex items-center gap-4 mb-8">
                <div className="w-12 h-12 rounded-xl bg-primary-container flex items-center justify-center">
                  <svg className="w-6 h-6 text-on-primary" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-headline font-bold text-2xl text-white">The PokerFX Way</h3>
                  <p className="text-xs text-primary-container font-label uppercase tracking-widest">AI-Powered Workflow</p>
                </div>
              </div>
              <ul className="space-y-6 mb-12">
                {pokerfxWayBenefits.map((item) => (
                  <li key={item.title} className="flex items-start gap-4">
                    <svg className="w-5 h-5 text-primary-container mt-1 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div>
                      <h4 className="text-white font-bold text-sm mb-1">{item.title}</h4>
                      <p className="text-sm text-on-surface-variant">{item.desc}</p>
                    </div>
                  </li>
                ))}
              </ul>
              <div className="bg-primary-container/10 rounded-2xl p-6 border border-primary-container/20">
                <div className="text-3xl font-headline font-bold text-primary-container mb-1">5 Minutes</div>
                <div className="text-xs font-label text-gray-500 uppercase tracking-widest">Per 10-Minute Vlog</div>
              </div>
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-16 flex flex-col items-center">
          <p className="text-gray-500 font-headline font-medium mb-6">
            Saving you an average of <span className="text-white">40+ hours per month</span>
          </p>
          <div className="h-1.5 w-full max-w-lg bg-surface-container-high rounded-full overflow-hidden flex">
            <div className="h-full bg-primary-container w-[98%] shadow-[0_0_10px_rgba(57,255,20,0.5)]" />
            <div className="h-full bg-error w-[2%]" />
          </div>
        </div>
      </div>
    </section>
  );
}
