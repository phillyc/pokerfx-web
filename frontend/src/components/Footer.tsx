const currentYear = new Date().getFullYear();

export default function Footer() {
  return (
    <footer className="bg-surface-container-lowest border-t border-outline-variant/15">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-start">
          {/* Branding */}
          <div>
            <p className="text-primary-fixed-dim font-black text-xl font-headline tracking-tighter">
              PokerFX
            </p>
            <p className="text-on-surface-variant text-sm mt-2 font-body">
              Automated precision for the modern grinder.
            </p>
          </div>

          {/* Legal */}
          <div className="flex flex-col gap-2">
            <a href="/privacy" className="text-on-surface-variant hover:text-primary transition-colors text-sm">
              Privacy Policy
            </a>
            <a href="/terms" className="text-on-surface-variant hover:text-primary transition-colors text-sm">
              Terms of Service
            </a>
          </div>

          {/* Community */}
          <div className="flex flex-col gap-2">
            <a
              href="https://discord.gg/nofacepoker"
              target="_blank"
              rel="noopener noreferrer"
              className="text-on-surface-variant hover:text-primary transition-colors text-sm"
            >
              Discord Community
            </a>
            <a
              href="https://nofacepoker.com/affiliate"
              target="_blank"
              rel="noopener noreferrer"
              className="text-on-surface-variant hover:text-primary transition-colors text-sm"
            >
              Affiliate Program
            </a>
          </div>
        </div>

        {/* Copyright */}
        <div className="border-t border-outline-variant/15 mt-8 pt-6 text-center">
          <p className="text-on-surface-variant text-xs font-label tracking-wider">
            &copy; {currentYear} PokerFX. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
