import ComparisonSection from '../components/ComparisonSection';
import FeatureGrid from '../components/FeatureGrid';
import { Link } from 'react-router-dom';

export default function LandingPage() {
  return (
    <>
      {/* Hero Section */}
      <section className="relative min-h-[92vh] flex items-center overflow-hidden">
        {/* Ambient glow */}
        <div className="absolute inset-0 z-0">
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/80 to-background" />
          {/* TODO: Swap for real hero image from assets/hero.png */}
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-primary-container/5 via-background to-background" />
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-6 py-24 w-full">
          <div className="max-w-3xl">
            {/* Version badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-surface-container-low border border-outline-variant/15 rounded-full mb-6">
              <span className="flex h-2 w-2 rounded-full bg-primary-container animate-pulse" />
              <span className="text-xs font-label uppercase tracking-widest text-primary-fixed-dim">V2.0 is now live</span>
            </div>

            {/* Headline */}
            <h1 className="text-5xl md:text-7xl lg:text-8xl font-headline font-bold leading-[0.9] tracking-tighter mb-8 text-white">
              The Future of <span className="text-primary-container neon-glow">Poker Vlogging</span>
            </h1>

            {/* Subtitle */}
            <p className="text-xl text-on-surface-variant max-w-xl mb-10 leading-relaxed">
              Automated video animation and AI-powered editing. Transform raw hand footage into high-stakes broadcast productions in seconds.
            </p>

            {/* CTAs */}
            <div className="flex flex-wrap gap-4">
              <Link
                to="/upload"
                className="px-8 py-4 bg-primary-container text-on-primary font-headline font-bold text-lg rounded-xl hover:shadow-[0_0_30px_rgba(57,255,20,0.4)] transition-all flex items-center gap-2 active:scale-[0.98]"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                </svg>
                Get Started Free
              </Link>
              <button
                className="px-8 py-4 glass-card text-white font-headline font-bold text-lg rounded-xl hover:bg-surface-variant transition-all flex items-center gap-2"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                  <circle cx="12" cy="12" r="10" />
                  <path d="M10 8l6 4-6 4V8z" fill="currentColor" />
                </svg>
                Watch Showcase
              </button>
            </div>

            {/* Stats */}
            <div className="mt-12 flex items-center gap-8">
              <div className="flex flex-col">
                <span className="text-3xl font-headline font-bold text-white">1.2M+</span>
                <span className="text-xs text-gray-500 font-label uppercase tracking-widest">Hands Processed</span>
              </div>
              <div className="w-px h-10 bg-outline-variant/20" />
              <div className="flex flex-col">
                <span className="text-3xl font-headline font-bold text-white">99.8%</span>
                <span className="text-xs text-gray-500 font-label uppercase tracking-widest">AI Accuracy</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Comparison Section */}
      <ComparisonSection />

      {/* Feature Grid */}
      <FeatureGrid />
    </>
  );
}
