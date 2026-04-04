import { useState } from 'react';
import { Link } from 'react-router-dom';

export default function Header() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 bg-background/95 backdrop-blur-sm shadow-[0_8px_32px_rgba(42,229,0,0.08)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link
            to="/"
            className="text-primary-fixed-dim font-black text-2xl font-headline tracking-tighter neon-glow"
          >
            PokerFX
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-on-surface hover:text-primary transition-colors text-sm font-medium">
              Features
            </a>
            <a href="#how-it-works" className="text-on-surface hover:text-primary transition-colors text-sm font-medium">
              How it Works
            </a>
            <a href="#pricing" className="text-on-surface hover:text-primary transition-colors text-sm font-medium">
              Pricing
            </a>
            <a href="#showcase" className="text-on-surface hover:text-primary transition-colors text-sm font-medium">
              Showcase
            </a>
          </nav>

          {/* Right Actions */}
          <div className="hidden md:flex items-center gap-4">
            <a
              href="/api/auth/session"
              className="text-on-surface hover:text-primary transition-colors text-sm font-medium"
            >
              Login
            </a>
            <Link
              to="/"
              className="bg-primary-container text-on-primary px-5 py-2 rounded-full text-sm font-semibold hover:bg-primary hover:opacity-90 transition-all active:scale-[0.98]"
            >
              Get Started
            </Link>
          </div>

          {/* Mobile Hamburger */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden p-2 text-on-surface hover:text-primary"
            aria-label="Toggle mobile menu"
          >
            {mobileOpen ? (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            )}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileOpen && (
          <div className="md:hidden pb-4 space-y-3">
            <a href="#features" className="block text-on-surface hover:text-primary transition-colors py-2 text-sm font-medium">
              Features
            </a>
            <a href="#how-it-works" className="block text-on-surface hover:text-primary transition-colors py-2 text-sm font-medium">
              How it Works
            </a>
            <a href="#pricing" className="block text-on-surface hover:text-primary transition-colors py-2 text-sm font-medium">
              Pricing
            </a>
            <a href="#showcase" className="block text-on-surface hover:text-primary transition-colors py-2 text-sm font-medium">
              Showcase
            </a>
            <div className="pt-2 space-y-2">
              <a href="/api/auth/session" className="block text-on-surface hover:text-primary transition-colors text-sm font-medium">
                Login
              </a>
              <Link
                to="/"
                className="inline-block bg-primary-container text-on-primary px-5 py-2 rounded-full text-sm font-semibold hover:bg-primary hover:opacity-90 transition-all active:scale-[0.98]"
              >
                Get Started
              </Link>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
