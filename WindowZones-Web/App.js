import React, { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Linking
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { LayoutSimulator } from './src/LayoutSimulator';
import {
  PRODUCT_INFO,
  PRICING_TIERS,
  FEATURE_COMPARISON,
  ROADMAP_PHASES,
  TRIAL_FLOW
} from './src/data';

export default function App() {
  const [email, setEmail] = useState('');
  const [subscribed, setSubscribed] = useState(false);

  const handleSubscribe = () => {
    if (email.trim().includes('@')) {
      setSubscribed(true);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>
      <StatusBar style="light" />

      {/* TOP NOTIFICATION BANNER */}
      <View style={styles.topBanner}>
        <View style={styles.topBannerInner}>
          <Text style={styles.topBannerTag}>COMMERCIAL PREVIEW</Text>
          <Text style={styles.topBannerText}>
            WindowZones is actively transitioning to a high-performance commercial desktop release.
          </Text>
          <Text style={styles.topBannerSub}>
            Perpetual licensing • Zero recurring monthly paywalls • 14-Day Reverse Trial
          </Text>
        </View>
      </View>

      {/* NAVIGATION BAR */}
      <View style={styles.navBar}>
        <View style={styles.navLogoContainer}>
          <View style={styles.logoBadge}>
            <Text style={styles.logoBadgeText}>WZ</Text>
          </View>
          <View>
            <Text style={styles.navLogoTitle}>{PRODUCT_INFO.name}</Text>
            <Text style={styles.navLogoSub}>Desktop Orchestrator</Text>
          </View>
        </View>

        <View style={styles.navActions}>
          <View style={styles.tagComingSoon}>
            <Text style={styles.tagComingSoonText}>COMING SOON</Text>
          </View>
        </View>
      </View>

      {/* HERO SECTION */}
      <View style={styles.heroSection}>
        <View style={styles.heroBadgeRow}>
          <Text style={styles.heroBadge}>WINDOWS 10 & 11 POWER UTILITY</Text>
          <Text style={styles.heroBadgeSub}>CLOSED SOURCE COMMERCIAL SUITE</Text>
        </View>

        <Text style={styles.heroHeadline}>
          Tame Massive Displays.{'\n'}Automate Window Geometry.
        </Text>

        <Text style={styles.heroSubhead}>
          {PRODUCT_INFO.tagline}. Designed for software engineers, traders, and ultrawide display enthusiasts who reject rigid grid snapping and monthly subscription fatigue.
        </Text>

        {/* EMAIL PRE-REGISTRATION / EARLY ACCESS */}
        <View style={styles.signupBox}>
          {subscribed ? (
            <View style={styles.subscribedConfirmation}>
              <Text style={styles.subscribedText}>
                ✓ You are on the VIP Early Access list! We will notify you when WindowZones launches.
              </Text>
            </View>
          ) : (
            <View style={styles.signupRow}>
              <TextInput
                style={styles.signupInput}
                placeholder="Enter work email for early access & 30% discount"
                placeholderTextColor="#6b7280"
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
              />
              <TouchableOpacity style={styles.btnPrimary} onPress={handleSubscribe}>
                <Text style={styles.btnPrimaryText}>Request Early Access</Text>
              </TouchableOpacity>
            </View>
          )}
          <Text style={styles.signupDisclaimer}>
            14-Day Reverse Trial included. No credit card required. Windows desktop installer.
          </Text>
        </View>

        {/* HERO STATS */}
        <View style={styles.statsRow}>
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>$24</Text>
            <Text style={styles.statLabel}>One-Time Perpetual License</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>14 Days</Text>
            <Text style={styles.statLabel}>100% Unlocked Reverse Trial</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>3 Devices</Text>
            <Text style={styles.statLabel}>Personal Activation Limit</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>Offline</Text>
            <Text style={styles.statLabel}>Ed25519 Crypto License</Text>
          </View>
        </View>
      </View>

      {/* INTERACTIVE DESKTOP SIMULATOR */}
      <LayoutSimulator />

      {/* REVERSE TRIAL PHILOSOPHY */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionOverline}>FRICTIONLESS ADOPTION</Text>
          <Text style={styles.sectionTitle}>The 14-Day "Reverse Trial" Model</Text>
          <Text style={styles.sectionDescription}>
            Window managers require muscle memory. Rigid 24-hour lockouts and upfront credit card demands kill workflow integration. WindowZones uses a user-first reverse trial.
          </Text>
        </View>

        <View style={styles.trialCardsRow}>
          {TRIAL_FLOW.map((t, idx) => (
            <View key={idx} style={styles.trialCard}>
              <View style={styles.trialCardHeader}>
                <Text style={styles.trialCardDay}>{t.day}</Text>
              </View>
              <Text style={styles.trialCardTitle}>{t.title}</Text>
              <Text style={styles.trialCardDesc}>{t.desc}</Text>
            </View>
          ))}
        </View>
      </View>

      {/* KEY COMMERCIAL FEATURES */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionOverline}>CLOSED SOURCE ADVANTAGES</Text>
          <Text style={styles.sectionTitle}>Architected for Real Desktop Workflows</Text>
          <Text style={styles.sectionDescription}>
            Standard Windows 11 snapping treats every window identically. WindowZones provides deep COM heuristics and sub-pixel Win32 compensation.
          </Text>
        </View>

        <View style={styles.featuresGrid}>
          <View style={styles.featureCard}>
            <Text style={styles.featureCardIcon}>🎯</Text>
            <Text style={styles.featureCardTitle}>Sub-Pixel DWM Border Correction</Text>
            <Text style={styles.featureCardText}>
              Windows 11 injects invisible 7px drop-shadow resize margins. WindowZones reads DWMWA_EXTENDED_FRAME_BOUNDS directly to align windows with mathematical precision.
            </Text>
          </View>

          <View style={styles.featureCard}>
            <Text style={styles.featureCardIcon}>📺</Text>
            <Text style={styles.featureCardTitle}>Intelligent PiP & PWA Recognition</Text>
            <Text style={styles.featureCardText}>
              Differentiates standalone web apps from browsing tabs via Windows UIAutomation COM tree inspection. Preserves strict aspect ratios like 16:9, 3:2, and 1:1.
            </Text>
          </View>

          <View style={styles.featureCard}>
            <Text style={styles.featureCardIcon}>⚡</Text>
            <Text style={styles.featureCardTitle}>Global Low-Latency Hotkeys</Text>
            <Text style={styles.featureCardText}>
              Instant zero-latency snapping with Win+Shift+Z, live preferences with Ctrl+Win+Z, and dynamic overlay reveal while holding the Ctrl drag modifier.
            </Text>
          </View>

          <View style={styles.featureCard}>
            <Text style={styles.featureCardIcon}>🖥️</Text>
            <Text style={styles.featureCardTitle}>Ultrawide (21:9 / 32:9) Presets</Text>
            <Text style={styles.featureCardText}>
              Splits expansive high-resolution displays into ergonomically balanced columns, placing focus code in the center and companions at exact pixel ratios.
            </Text>
          </View>

          <View style={styles.featureCard}>
            <Text style={styles.featureCardIcon}>🛡️</Text>
            <Text style={styles.featureCardTitle}>Offline Cryptographic Licensing</Text>
            <Text style={styles.featureCardText}>
              License keys are signed with Ed25519 asymmetric cryptography and verified locally. Never phones home. Zero server downtime risk.
            </Text>
          </View>

          <View style={styles.featureCard}>
            <Text style={styles.featureCardIcon}>🔕</Text>
            <Text style={styles.featureCardTitle}>Zero Terminal Windows</Text>
            <Text style={styles.featureCardText}>
              Runs silently in the Windows system tray with instantaneous right-click actions, balloon state notifications, and clean Windows startup integration.
            </Text>
          </View>
        </View>
      </View>

      {/* PRICING PLANS */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionOverline}>TRANSPARENT PRICING</Text>
          <Text style={styles.sectionTitle}>Simple, Perpetual Licensing</Text>
          <Text style={styles.sectionDescription}>
            Inspired by tools like Sublime Text and TablePlus. Buy once, own your version forever, and renew updates only if you want them.
          </Text>
        </View>

        <View style={styles.pricingRow}>
          {PRICING_TIERS.map((tier) => (
            <View
              key={tier.id}
              style={[styles.pricingCard, tier.highlight && styles.pricingCardHighlight]}
            >
              {tier.badge && (
                <View style={[styles.tierBadge, tier.highlight && styles.tierBadgeHighlight]}>
                  <Text style={styles.tierBadgeText}>{tier.badge}</Text>
                </View>
              )}

              <Text style={styles.tierName}>{tier.name}</Text>
              <Text style={styles.tierPrice}>{tier.price}</Text>
              <Text style={styles.tierBilling}>{tier.billing}</Text>
              <Text style={styles.tierDesc}>{tier.description}</Text>

              <View style={styles.tierFeaturesList}>
                {tier.features.map((f, i) => (
                  <View key={i} style={styles.tierFeatureItem}>
                    <Text style={styles.tierFeatureCheck}>✓</Text>
                    <Text style={styles.tierFeatureText}>{f}</Text>
                  </View>
                ))}
              </View>

              <TouchableOpacity
                style={[styles.tierCtaBtn, tier.highlight && styles.tierCtaBtnHighlight]}
                onPress={handleSubscribe}
              >
                <Text style={[styles.tierCtaText, tier.highlight && styles.tierCtaTextHighlight]}>
                  {tier.cta}
                </Text>
              </TouchableOpacity>
            </View>
          ))}
        </View>
      </View>

      {/* FEATURE COMPARISON TABLE */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionOverline}>EDITION BREAKDOWN</Text>
          <Text style={styles.sectionTitle}>Free Tier vs. WindowZones Pro</Text>
          <Text style={styles.sectionDescription}>
            Understand what remains active after your 14-day reverse trial.
          </Text>
        </View>

        <View style={styles.tableContainer}>
          <View style={styles.tableHeaderRow}>
            <Text style={[styles.tableColFeature, styles.tableHeaderTitle]}>Capability</Text>
            <Text style={[styles.tableColFree, styles.tableHeaderTitle]}>Free Tier</Text>
            <Text style={[styles.tableColPro, styles.tableHeaderTitle]}>Pro Tier ($24)</Text>
          </View>

          {FEATURE_COMPARISON.map((row, idx) => (
            <View key={idx} style={[styles.tableDataRow, idx % 2 === 1 && styles.tableRowAlt]}>
              <Text style={styles.tableColFeature}>{row.feature}</Text>
              <Text style={styles.tableColFree}>{row.free}</Text>
              <Text style={styles.tableColPro}>{row.pro}</Text>
            </View>
          ))}
        </View>
      </View>

      {/* ARCHITECTURE ROADMAP */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionOverline}>ENGINEERING ARCHITECTURE</Text>
          <Text style={styles.sectionTitle}>Phased Migration Roadmap</Text>
          <Text style={styles.sectionDescription}>
            WindowZones follows an engineered 3-phase strategy: rapid prototype logic validation in Python, hybrid Tauri integration, followed by a standalone pure Rust native binary.
          </Text>
        </View>

        <View style={styles.roadmapContainer}>
          {ROADMAP_PHASES.map((p, idx) => (
            <View key={idx} style={styles.roadmapCard}>
              <View style={styles.roadmapCardHeader}>
                <View>
                  <Text style={styles.roadmapPhaseTitle}>{p.phase}</Text>
                  <Text style={[styles.roadmapStatus, p.current && { color: '#38bdf8' }]}>
                    {p.status}
                  </Text>
                </View>
                <View style={[styles.phaseNumberBadge, p.current && styles.phaseNumberBadgeCurrent]}>
                  <Text style={styles.phaseNumberText}>0{idx + 1}</Text>
                </View>
              </View>

              <View style={styles.roadmapPointsList}>
                {p.points.map((pt, i) => (
                  <View key={i} style={styles.roadmapPointItem}>
                    <Text style={styles.roadmapBullet}>•</Text>
                    <Text style={styles.roadmapPointText}>{pt}</Text>
                  </View>
                ))}
              </View>
            </View>
          ))}
        </View>
      </View>

      {/* FINAL CALL TO ACTION */}
      <View style={styles.ctaBanner}>
        <Text style={styles.ctaBannerTitle}>Ready to Reclaim Your Workspace?</Text>
        <Text style={styles.ctaBannerText}>
          Pre-register for WindowZones today to secure priority access and locked-in launch pricing.
        </Text>
        <View style={styles.ctaButtonRow}>
          <TouchableOpacity style={styles.btnPrimary} onPress={handleSubscribe}>
            <Text style={styles.btnPrimaryText}>Join Early Access List</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* FOOTER */}
      <View style={styles.footer}>
        <View style={styles.footerInner}>
          <Text style={styles.footerBrand}>WindowZones</Text>
          <Text style={styles.footerCopy}>
            © 2026 WindowZones. Commercial Desktop Software. All Rights Reserved.
          </Text>
          <Text style={styles.footerNote}>
            Designed for Windows 10 & 11 (x64 / ARM64). Powered by offline Ed25519 licensing.
          </Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#09090b',
  },
  scrollContent: {
    paddingBottom: 40,
  },
  topBanner: {
    backgroundColor: '#18181b',
    borderBottomWidth: 1,
    borderBottomColor: '#27272a',
    paddingVertical: 10,
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  topBannerInner: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  topBannerTag: {
    fontSize: 10,
    fontWeight: '800',
    backgroundColor: '#3b82f6',
    color: '#ffffff',
    paddingVertical: 2,
    paddingHorizontal: 6,
    borderRadius: 4,
    letterSpacing: 0.8,
  },
  topBannerText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#e4e4e7',
  },
  topBannerSub: {
    fontSize: 12,
    color: '#a1a1aa',
  },
  navBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 32,
    paddingVertical: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#18181b',
    maxWidth: 1200,
    width: '100%',
    alignSelf: 'center',
  },
  navLogoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  logoBadge: {
    width: 38,
    height: 38,
    borderRadius: 10,
    backgroundColor: '#3b82f6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoBadgeText: {
    color: '#ffffff',
    fontWeight: '800',
    fontSize: 16,
  },
  navLogoTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#ffffff',
    letterSpacing: 0.5,
  },
  navLogoSub: {
    fontSize: 11,
    color: '#71717a',
  },
  navActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  tagComingSoon: {
    backgroundColor: 'rgba(59, 130, 246, 0.12)',
    borderColor: '#3b82f6',
    borderWidth: 1,
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 20,
  },
  tagComingSoonText: {
    color: '#60a5fa',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.8,
  },
  heroSection: {
    alignItems: 'center',
    paddingTop: 56,
    paddingBottom: 40,
    paddingHorizontal: 20,
    maxWidth: 960,
    alignSelf: 'center',
    width: '100%',
  },
  heroBadgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 16,
    backgroundColor: '#18181b',
    paddingVertical: 6,
    paddingHorizontal: 14,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: '#27272a',
  },
  heroBadge: {
    fontSize: 11,
    fontWeight: '700',
    color: '#a1a1aa',
    letterSpacing: 0.8,
  },
  heroBadgeSub: {
    fontSize: 11,
    fontWeight: '700',
    color: '#38bdf8',
    letterSpacing: 0.8,
  },
  heroHeadline: {
    fontSize: 44,
    fontWeight: '800',
    color: '#ffffff',
    textAlign: 'center',
    lineHeight: 52,
    marginBottom: 16,
  },
  heroSubhead: {
    fontSize: 17,
    color: '#a1a1aa',
    textAlign: 'center',
    lineHeight: 26,
    marginBottom: 32,
    maxWidth: 720,
  },
  signupBox: {
    width: '100%',
    maxWidth: 600,
    marginBottom: 40,
  },
  signupRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 8,
  },
  signupInput: {
    flex: 1,
    backgroundColor: '#18181b',
    borderWidth: 1,
    borderColor: '#27272a',
    borderRadius: 10,
    paddingHorizontal: 16,
    paddingVertical: 14,
    color: '#ffffff',
    fontSize: 14,
  },
  btnPrimary: {
    backgroundColor: '#3b82f6',
    paddingHorizontal: 22,
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  btnPrimaryText: {
    color: '#ffffff',
    fontWeight: '700',
    fontSize: 14,
  },
  signupDisclaimer: {
    fontSize: 11,
    color: '#71717a',
    textAlign: 'center',
  },
  subscribedConfirmation: {
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    borderWidth: 1,
    borderColor: '#10b981',
    borderRadius: 10,
    padding: 16,
    marginBottom: 8,
  },
  subscribedText: {
    color: '#34d399',
    fontSize: 13,
    fontWeight: '600',
    textAlign: 'center',
  },
  statsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#111115',
    borderWidth: 1,
    borderColor: '#1e1e24',
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 24,
    width: '100%',
    gap: 20,
  },
  statItem: {
    alignItems: 'center',
    minWidth: 120,
  },
  statNumber: {
    fontSize: 22,
    fontWeight: '800',
    color: '#ffffff',
    marginBottom: 2,
  },
  statLabel: {
    fontSize: 11,
    color: '#71717a',
    fontWeight: '500',
  },
  statDivider: {
    width: 1,
    height: 32,
    backgroundColor: '#27272a',
  },
  section: {
    paddingVertical: 48,
    paddingHorizontal: 20,
    maxWidth: 1100,
    alignSelf: 'center',
    width: '100%',
  },
  sectionHeader: {
    alignItems: 'center',
    marginBottom: 36,
  },
  sectionOverline: {
    fontSize: 11,
    fontWeight: '800',
    color: '#38bdf8',
    letterSpacing: 1.5,
    marginBottom: 6,
  },
  sectionTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#ffffff',
    textAlign: 'center',
    marginBottom: 10,
  },
  sectionDescription: {
    fontSize: 15,
    color: '#a1a1aa',
    textAlign: 'center',
    maxWidth: 680,
    lineHeight: 22,
  },
  trialCardsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 20,
    justifyContent: 'center',
  },
  trialCard: {
    flex: 1,
    minWidth: 280,
    backgroundColor: '#121217',
    borderWidth: 1,
    borderColor: '#24242e',
    borderRadius: 12,
    padding: 24,
  },
  trialCardHeader: {
    marginBottom: 12,
  },
  trialCardDay: {
    fontSize: 11,
    fontWeight: '800',
    color: '#3b82f6',
    backgroundColor: 'rgba(59, 130, 246, 0.12)',
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  trialCardTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: 8,
  },
  trialCardDesc: {
    fontSize: 13,
    color: '#9ca3af',
    lineHeight: 20,
  },
  featuresGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 20,
    justifyContent: 'center',
  },
  featureCard: {
    width: '31%',
    minWidth: 260,
    backgroundColor: '#111115',
    borderWidth: 1,
    borderColor: '#202028',
    borderRadius: 12,
    padding: 22,
  },
  featureCardIcon: {
    fontSize: 26,
    marginBottom: 14,
  },
  featureCardTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: 8,
  },
  featureCardText: {
    fontSize: 13,
    color: '#9ca3af',
    lineHeight: 19,
  },
  pricingRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 20,
    justifyContent: 'center',
  },
  pricingCard: {
    flex: 1,
    minWidth: 290,
    backgroundColor: '#111115',
    borderWidth: 1,
    borderColor: '#22222b',
    borderRadius: 14,
    padding: 28,
    position: 'relative',
  },
  pricingCardHighlight: {
    borderColor: '#3b82f6',
    backgroundColor: '#131520',
  },
  tierBadge: {
    position: 'absolute',
    top: 14,
    right: 14,
    backgroundColor: '#272733',
    paddingVertical: 3,
    paddingHorizontal: 10,
    borderRadius: 12,
  },
  tierBadgeHighlight: {
    backgroundColor: '#3b82f6',
  },
  tierBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#ffffff',
    letterSpacing: 0.5,
  },
  tierName: {
    fontSize: 18,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: 6,
  },
  tierPrice: {
    fontSize: 34,
    fontWeight: '800',
    color: '#ffffff',
    marginBottom: 2,
  },
  tierBilling: {
    fontSize: 12,
    color: '#9ca3af',
    marginBottom: 12,
  },
  tierDesc: {
    fontSize: 13,
    color: '#94a3b8',
    lineHeight: 18,
    marginBottom: 20,
  },
  tierFeaturesList: {
    marginBottom: 24,
    gap: 10,
  },
  tierFeatureItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
  },
  tierFeatureCheck: {
    color: '#10b981',
    fontWeight: '700',
    fontSize: 14,
  },
  tierFeatureText: {
    fontSize: 12,
    color: '#cbd5e1',
    flex: 1,
    lineHeight: 18,
  },
  tierCtaBtn: {
    backgroundColor: '#1e1e28',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 'auto',
  },
  tierCtaBtnHighlight: {
    backgroundColor: '#3b82f6',
  },
  tierCtaText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#ffffff',
  },
  tierCtaTextHighlight: {
    color: '#ffffff',
  },
  tableContainer: {
    backgroundColor: '#111115',
    borderWidth: 1,
    borderColor: '#202028',
    borderRadius: 12,
    overflow: 'hidden',
  },
  tableHeaderRow: {
    flexDirection: 'row',
    backgroundColor: '#181820',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#252532',
  },
  tableHeaderTitle: {
    fontWeight: '700',
    color: '#ffffff',
    fontSize: 13,
  },
  tableDataRow: {
    flexDirection: 'row',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1a1a22',
  },
  tableRowAlt: {
    backgroundColor: '#14141a',
  },
  tableColFeature: {
    flex: 3,
    fontSize: 13,
    color: '#cbd5e1',
  },
  tableColFree: {
    flex: 1.5,
    fontSize: 12,
    color: '#94a3b8',
  },
  tableColPro: {
    flex: 1.8,
    fontSize: 12,
    fontWeight: '600',
    color: '#38bdf8',
  },
  roadmapContainer: {
    gap: 16,
  },
  roadmapCard: {
    backgroundColor: '#111115',
    borderWidth: 1,
    borderColor: '#202028',
    borderRadius: 12,
    padding: 22,
  },
  roadmapCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 14,
  },
  roadmapPhaseTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: 2,
  },
  roadmapStatus: {
    fontSize: 12,
    color: '#9ca3af',
    fontWeight: '600',
  },
  phaseNumberBadge: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: '#1f1f2b',
    alignItems: 'center',
    justifyContent: 'center',
  },
  phaseNumberBadgeCurrent: {
    backgroundColor: '#0284c7',
  },
  phaseNumberText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#ffffff',
  },
  roadmapPointsList: {
    gap: 6,
  },
  roadmapPointItem: {
    flexDirection: 'row',
    gap: 8,
  },
  roadmapBullet: {
    color: '#38bdf8',
    fontSize: 14,
  },
  roadmapPointText: {
    fontSize: 13,
    color: '#9ca3af',
    flex: 1,
    lineHeight: 18,
  },
  ctaBanner: {
    backgroundColor: '#131522',
    borderWidth: 1,
    borderColor: '#252945',
    borderRadius: 16,
    padding: 40,
    marginHorizontal: 20,
    marginTop: 20,
    marginBottom: 40,
    maxWidth: 960,
    alignSelf: 'center',
    alignItems: 'center',
    width: '100%',
  },
  ctaBannerTitle: {
    fontSize: 26,
    fontWeight: '800',
    color: '#ffffff',
    textAlign: 'center',
    marginBottom: 10,
  },
  ctaBannerText: {
    fontSize: 14,
    color: '#94a3b8',
    textAlign: 'center',
    maxWidth: 580,
    marginBottom: 24,
    lineHeight: 20,
  },
  ctaButtonRow: {
    flexDirection: 'row',
    gap: 12,
  },
  footer: {
    borderTopWidth: 1,
    borderTopColor: '#18181b',
    paddingVertical: 32,
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  footerInner: {
    alignItems: 'center',
    gap: 6,
  },
  footerBrand: {
    fontSize: 15,
    fontWeight: '700',
    color: '#ffffff',
  },
  footerCopy: {
    fontSize: 12,
    color: '#71717a',
  },
  footerNote: {
    fontSize: 11,
    color: '#52525b',
  },
});