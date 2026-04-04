import { Link } from 'react-router-dom';
import heroImg from '../assets/hero.png';

const workflowSteps = [
  {
    num: '01',
    title: 'Ingest',
    desc: 'Raw sessions uploaded or linked. Supports MP4, MOV, or direct OBS output.',
  },
  {
    num: '02',
    title: 'Analyze',
    desc: 'Neural networks detect pots, bets, and card reveals frame by frame.',
  },
  {
    num: '03',
    title: 'Render',
    desc: 'Export in 9:16 (TikTok/Shorts) or 16:9 (YouTube) with one click.',
  },
];

const timelineItems = [
  { status: 'done', label: 'Frame detection complete' },
  { status: 'done', label: 'Hole cards identified' },
  { status: 'done', label: 'Face blur applied' },
  { status: 'active', label: 'Rendering at 4K...' },
];

export default function WorkflowSection() {
  return (
    <section id="how-it-works" className="py-24 bg-surface-container-lowest/50">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
          {/* Left Side — Process Timeline Mockup */}
          <div className="order-2 lg:order-1 relative">
            <div className="absolute -inset-10 bg-secondary-container/5 blur-[120px] rounded-full" />
            <div className="relative glass-card p-4 rounded-2xl shadow-2xl">
              {/* Two Preview Windows */}
              <div className="grid grid-cols-2 gap-4">
                {/* RAW FOOTAGE */}
                <div className="relative aspect-square bg-surface-container rounded-xl overflow-hidden border border-white/5 group">
                  <img
                    src={heroImg}
                    alt="Raw footage from poker table"
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-surface-container/80 to-transparent" />
                  <span className="absolute bottom-3 left-3 text-[10px] font-label uppercase tracking-widest text-gray-400">
                    Raw Footage
                  </span>
                </div>

                {/* AI PROCESSED */}
                <div className="relative aspect-square bg-surface-container rounded-xl overflow-hidden border border-white/5 flex items-center justify-center">
                  <img
                    src={heroImg}
                    alt="AI processed footage with green tracking overlay"
                    className="w-full h-full object-cover grayscale opacity-40"
                  />
                  <div className="absolute inset-0 bg-primary-container/10 backdrop-blur-[1px] flex items-center justify-center">
                    <div className="w-16 h-16 border-2 border-primary-container rounded-lg flex items-center justify-center font-headline font-black text-2xl text-primary-container shadow-[0_0_20px_rgba(57,255,20,0.3)]">
                      AA
                    </div>
                  </div>
                  <span className="absolute bottom-3 left-3 text-[10px] font-label uppercase tracking-widest text-primary-container">
                    AI Processed
                  </span>
                </div>
              </div>

              {/* Process Timeline */}
              <div className="mt-4 p-4 bg-surface-container rounded-xl border border-white/5">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs font-label text-gray-500 uppercase">Process Timeline</span>
                  <span className="text-xs font-label text-primary-container">87% Complete</span>
                </div>
                <div className="h-1.5 w-full bg-surface-variant rounded-full overflow-hidden">
                  <div className="h-full w-[87%] bg-gradient-to-r from-primary-container to-primary-fixed rounded-full" />
                </div>
                <div className="mt-6 space-y-3">
                  {timelineItems.map((item) => (
                    <div
                      key={item.label}
                      className={`flex items-center gap-3 text-sm ${
                        item.status === 'active'
                          ? 'text-white font-medium'
                          : 'text-on-surface-variant'
                      }`}
                    >
                      {item.status === 'done' ? (
                        <svg className="w-5 h-5 text-primary-container shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      ) : (
                        <span className="flex h-2 w-2 bg-primary-container rounded-full animate-ping shrink-0" />
                      )}
                      {item.label}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Right Side — Step-by-Step Guide */}
          <div className="order-1 lg:order-2">
            <h2 className="text-4xl md:text-5xl font-headline font-bold mb-6 text-white tracking-tight leading-tight">
              From <span className="text-secondary-container">Raw Footage</span> to Viral Clips.
            </h2>
            <p className="text-lg text-on-surface-variant mb-8 leading-relaxed">
              Our workflow is designed for the modern creator. Drag and drop your raw table footage, and let our engine extract the drama, highlight the sizing, and export ready-to-post content.
            </p>

            <div className="space-y-6 relative">
              {/* Connecting line */}
              <div className="hidden lg:block absolute left-5 top-10 bottom-10 w-px bg-outline-variant/20" />

              {workflowSteps.map((step, idx) => (
                <div key={step.num} className="flex gap-4 items-start relative">
                  <div className="w-10 h-10 rounded-lg bg-surface-container-high flex items-center justify-center shrink-0 border border-outline-variant/20 relative z-10">
                    <span className="text-primary-container font-headline font-bold">{step.num}</span>
                  </div>
                  <div>
                    <h4 className="text-white font-headline font-bold mb-1">{step.title}</h4>
                    <p className="text-sm text-on-surface-variant">{step.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
