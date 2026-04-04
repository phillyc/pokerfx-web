import { Link } from 'react-router-dom';

export default function CTASection() {
  return (
    <section id="pricing" className="py-24 max-w-5xl mx-auto px-6 text-center">
      <div className="glass-card rounded-[2.5rem] p-12 md:p-20 relative overflow-hidden">
        {/* Decorative watermark */}
        <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
          <svg className="w-36 h-36" viewBox="0 0 24 24" fill="currentColor">
            <path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z" />
          </svg>
        </div>

        <h2 className="text-4xl md:text-6xl font-headline font-bold mb-6 text-white tracking-tighter">
          Ready to <span className="text-primary-container neon-glow">Level Up</span> your content?
        </h2>
        <p className="text-lg text-on-surface-variant mb-12 max-w-2xl mx-auto">
          Join thousands of poker vloggers who automate their editing pipeline with PokerFX.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/upload"
            className="px-10 py-5 bg-primary-container text-on-primary font-headline font-black text-xl rounded-2xl hover:shadow-[0_0_40px_rgba(57,255,20,0.5)] transition-all active:scale-[0.98]"
          >
            START FREE TRIAL
          </Link>
          <a
            href="#pricing"
            className="px-10 py-5 bg-white/5 text-white font-headline font-bold text-xl rounded-2xl border border-white/10 hover:bg-white/10 transition-all"
          >
            VIEW PRICING
          </a>
        </div>
      </div>
    </section>
  );
}
