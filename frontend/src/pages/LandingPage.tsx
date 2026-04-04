import HeroSection from '../components/HeroSection';
import ComparisonSection from '../components/ComparisonSection';
import FeatureGrid from '../components/FeatureGrid';

export default function LandingPage() {
  return (
    <>
      {/* Hero */}
      <HeroSection />

      {/* Comparison */}
      <ComparisonSection />

      {/* Feature Grid */}
      <FeatureGrid />
    </>
  );
}
