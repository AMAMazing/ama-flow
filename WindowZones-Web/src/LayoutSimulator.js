import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

export const LayoutSimulator = () => {
  const [mode, setMode] = useState('3_window'); // '3_window' | 'corner'
  const [vscodeSide, setVscodeSide] = useState('Right');
  const [chromeSize, setChromeSize] = useState('432px');
  const [corner, setCorner] = useState('Bottom-Right');
  const [activeMediaRatio, setActiveMediaRatio] = useState('16:9');
  const [isMediaActive, setIsMediaActive] = useState(true);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View>
          <View style={styles.liveBadgeRow}>
            <View style={styles.statusDot} />
            <Text style={styles.badgeText}>INTERACTIVE DESKTOP SIMULATOR</Text>
          </View>
          <Text style={styles.title}>Test the WindowZones Layout Engine Live</Text>
          <Text style={styles.subtitle}>
            Experience how WindowZones dynamically arranges your IDE, browser companion, and media stream based on real aspect ratios.
          </Text>
        </View>

        <View style={styles.modeTabs}>
          <TouchableOpacity
            style={[styles.modeTab, mode === '3_window' && styles.modeTabActive]}
            onPress={() => setMode('3_window')}
          >
            <Text style={[styles.modeTabText, mode === '3_window' && styles.modeTabTextActive]}>
              3-Window Dynamic Split
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.modeTab, mode === 'corner' && styles.modeTabActive]}
            onPress={() => setMode('corner')}
          >
            <Text style={[styles.modeTabText, mode === 'corner' && styles.modeTabTextActive]}>
              Corner PiP Docking
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.controlsBar}>
        {mode === '3_window' ? (
          <>
            <View style={styles.controlGroup}>
              <Text style={styles.controlLabel}>VS CODE POSITION</Text>
              <View style={styles.segmentedRow}>
                {['Left', 'Right'].map((side) => (
                  <TouchableOpacity
                    key={side}
                    style={[styles.segmentBtn, vscodeSide === side && styles.segmentBtnActive]}
                    onPress={() => setVscodeSide(side)}
                  >
                    <Text style={[styles.segmentBtnText, vscodeSide === side && styles.segmentBtnTextActive]}>
                      {side}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <View style={styles.controlGroup}>
              <Text style={styles.controlLabel}>CHROME COMPANION</Text>
              <View style={styles.segmentedRow}>
                {['Equal', '432px', '590px'].map((sz) => (
                  <TouchableOpacity
                    key={sz}
                    style={[styles.segmentBtn, chromeSize === sz && styles.segmentBtnActive]}
                    onPress={() => setChromeSize(sz)}
                  >
                    <Text style={[styles.segmentBtnText, chromeSize === sz && styles.segmentBtnTextActive]}>
                      {sz}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <View style={styles.controlGroup}>
              <Text style={styles.controlLabel}>ACTIVE MEDIA</Text>
              <View style={styles.segmentedRow}>
                <TouchableOpacity
                  style={[styles.segmentBtn, isMediaActive && styles.segmentBtnActive]}
                  onPress={() => setIsMediaActive(!isMediaActive)}
                >
                  <Text style={[styles.segmentBtnText, isMediaActive && styles.segmentBtnTextActive]}>
                    {isMediaActive ? 'Detected (Active)' : 'None (50/50)'}
                  </Text>
                </TouchableOpacity>
                {isMediaActive &&
                  ['16:9', '3:2', '1:1'].map((ar) => (
                    <TouchableOpacity
                      key={ar}
                      style={[styles.segmentBtn, activeMediaRatio === ar && styles.segmentBtnActive]}
                      onPress={() => setActiveMediaRatio(ar)}
                    >
                      <Text style={[styles.segmentBtnText, activeMediaRatio === ar && styles.segmentBtnTextActive]}>
                        {ar}
                      </Text>
                    </TouchableOpacity>
                  ))}
              </View>
            </View>
          </>
        ) : (
          <View style={styles.controlGroup}>
            <Text style={styles.controlLabel}>CORNER DOCKING QUADRANT</Text>
            <View style={styles.segmentedRow}>
              {['Bottom-Right', 'Bottom-Left', 'Top-Right', 'Top-Left'].map((c) => (
                <TouchableOpacity
                  key={c}
                  style={[styles.segmentBtn, corner === c && styles.segmentBtnActive]}
                  onPress={() => setCorner(c)}
                >
                  <Text style={[styles.segmentBtnText, corner === c && styles.segmentBtnTextActive]}>
                    {c}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        )}
      </View>

      <View style={styles.monitorFrame}>
        <View style={styles.monitorHeader}>
          <View style={styles.windowControls}>
            <View style={[styles.windowDot, { backgroundColor: '#ff5f56' }]} />
            <View style={[styles.windowDot, { backgroundColor: '#ffbd2e' }]} />
            <View style={[styles.windowDot, { backgroundColor: '#27c93f' }]} />
          </View>
          <Text style={styles.monitorResolution}>
            Primary Display: 1920 x 1080 (Windows 11 Extended Frame Bounds Adjusted)
          </Text>
          <Text style={styles.hotkeyHint}>Hold [Ctrl] to reveal snap zones</Text>
        </View>

        <View style={styles.screenContent}>
          {mode === '3_window' ? (
            <View style={[styles.threeWinContainer, vscodeSide === 'Left' && { flexDirection: 'row-reverse' }]}>
              <View style={[styles.companionColumn, chromeSize === 'Equal' && { flex: 1 }]}>
                {isMediaActive ? (
                  <>
                    <View style={styles.zoneBoxChrome}>
                      <View style={styles.zoneTagRow}>
                        <Text style={styles.zoneTagRole}>COMPANION</Text>
                        <Text style={styles.zoneDimTag}>Height: {chromeSize === 'Equal' ? '50%' : chromeSize}</Text>
                      </View>
                      <Text style={styles.zoneTitle}>Google Chrome (Docs / PR Review)</Text>
                      <Text style={styles.zoneSub}>Automatic resize with 0px Win32 margin bleed</Text>
                    </View>

                    <View style={styles.zoneBoxMedia}>
                      <View style={styles.zoneTagRow}>
                        <Text style={[styles.zoneTagRole, { backgroundColor: '#0284c7' }]}>MEDIA STREAM</Text>
                        <Text style={styles.zoneDimTag}>Ratio: {activeMediaRatio}</Text>
                      </View>
                      <Text style={styles.zoneTitle}>Picture-in-Picture / PWA</Text>
                      <Text style={styles.zoneSub}>
                        Aspect ratio locked. Smart detection matched.
                      </Text>
                    </View>
                  </>
                ) : (
                  <View style={[styles.zoneBoxChrome, { flex: 1 }]}>
                    <View style={styles.zoneTagRow}>
                      <Text style={styles.zoneTagRole}>COMPANION</Text>
                      <Text style={styles.zoneDimTag}>Height: 100% (No Media)</Text>
                    </View>
                    <Text style={styles.zoneTitle}>Google Chrome</Text>
                    <Text style={styles.zoneSub}>Expanded to full vertical height</Text>
                  </View>
                )}
              </View>

              <View style={styles.zoneBoxVscode}>
                <View style={styles.zoneTagRow}>
                  <Text style={[styles.zoneTagRole, { backgroundColor: '#6366f1' }]}>PRIMARY WORKSPACE</Text>
                  <Text style={styles.zoneDimTag}>Full Height 1080px</Text>
                </View>
                <Text style={styles.zoneTitle}>Visual Studio Code</Text>
                <Text style={styles.zoneSub}>Focused code editing zone with zero distractions</Text>
              </View>
            </View>
          ) : (
            <View style={styles.cornerContainer}>
              <View style={styles.cornerMainApp}>
                <View style={styles.zoneTagRow}>
                  <Text style={[styles.zoneTagRole, { backgroundColor: '#6366f1' }]}>PRIMARY WORKSPACE</Text>
                  <Text style={styles.zoneDimTag}>1920 x 1080 Fullscreen</Text>
                </View>
                <Text style={styles.zoneTitle}>Visual Studio Code</Text>
                <Text style={styles.zoneSub}>Fullscreen focus mode active</Text>
              </View>

              <View
                style={[
                  styles.cornerOverlayWidget,
                  corner === 'Bottom-Right' && { bottom: 16, right: 16 },
                  corner === 'Bottom-Left' && { bottom: 16, left: 16 },
                  corner === 'Top-Right' && { top: 16, right: 16 },
                  corner === 'Top-Left' && { top: 16, left: 16 },
                ]}
              >
                <View style={styles.zoneTagRow}>
                  <Text style={[styles.zoneTagRole, { backgroundColor: '#0284c7' }]}>PINNED CORNER PiP</Text>
                  <Text style={styles.zoneDimTag}>16:9 Ratio</Text>
                </View>
                <Text style={[styles.zoneTitle, { fontSize: 13 }]}>Picture in Picture</Text>
                <Text style={[styles.zoneSub, { fontSize: 11 }]}>
                  Always-on-top corner anchor over active editor
                </Text>
              </View>
            </View>
          )}
        </View>

        <View style={styles.monitorFooter}>
          <Text style={styles.monitorFooterText}>
            Status: Engine Online | Hotkeys Registered: [Ctrl+Win+Z] Preferences | [Win+Shift+Z] Apply Layout
          </Text>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#111115',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#22222a',
    padding: 24,
    marginVertical: 32,
  },
  header: {
    marginBottom: 20,
  },
  liveBadgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#10b981',
    marginRight: 8,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#10b981',
    letterSpacing: 1.2,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: 6,
  },
  subtitle: {
    fontSize: 14,
    color: '#9ca3af',
    maxWidth: 720,
    lineHeight: 20,
  },
  modeTabs: {
    flexDirection: 'row',
    marginTop: 16,
    backgroundColor: '#18181f',
    padding: 4,
    borderRadius: 10,
    alignSelf: 'flex-start',
  },
  modeTab: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  modeTabActive: {
    backgroundColor: '#272733',
  },
  modeTabText: {
    fontSize: 13,
    color: '#828292',
    fontWeight: '600',
  },
  modeTabTextActive: {
    color: '#ffffff',
  },
  controlsBar: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 16,
    paddingVertical: 14,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: '#1e1e28',
    marginBottom: 20,
  },
  controlGroup: {
    marginRight: 16,
  },
  controlLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: '#6b7280',
    marginBottom: 6,
    letterSpacing: 0.8,
  },
  segmentedRow: {
    flexDirection: 'row',
    backgroundColor: '#18181f',
    borderRadius: 8,
    padding: 2,
  },
  segmentBtn: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 6,
  },
  segmentBtnActive: {
    backgroundColor: '#3b82f6',
  },
  segmentBtnText: {
    fontSize: 12,
    color: '#9ca3af',
    fontWeight: '600',
  },
  segmentBtnTextActive: {
    color: '#ffffff',
  },
  monitorFrame: {
    backgroundColor: '#0a0a0d',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#23232c',
    overflow: 'hidden',
  },
  monitorHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 10,
    backgroundColor: '#14141a',
    borderBottomWidth: 1,
    borderBottomColor: '#202028',
  },
  windowControls: {
    flexDirection: 'row',
    gap: 6,
  },
  windowDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  monitorResolution: {
    fontSize: 11,
    color: '#6b7280',
    fontWeight: '500',
  },
  hotkeyHint: {
    fontSize: 11,
    color: '#3b82f6',
    fontWeight: '600',
  },
  screenContent: {
    height: 380,
    padding: 12,
    backgroundColor: '#0c0c10',
  },
  threeWinContainer: {
    flex: 1,
    flexDirection: 'row',
    gap: 10,
  },
  companionColumn: {
    width: 260,
    gap: 10,
  },
  zoneBoxChrome: {
    flex: 1,
    backgroundColor: 'rgba(30, 41, 59, 0.45)',
    borderWidth: 1.5,
    borderColor: '#38bdf8',
    borderRadius: 8,
    padding: 12,
    justifyContent: 'center',
  },
  zoneBoxMedia: {
    height: 140,
    backgroundColor: 'rgba(2, 132, 199, 0.15)',
    borderWidth: 1.5,
    borderColor: '#0284c7',
    borderRadius: 8,
    padding: 12,
    justifyContent: 'center',
  },
  zoneBoxVscode: {
    flex: 1,
    backgroundColor: 'rgba(99, 102, 241, 0.12)',
    borderWidth: 1.5,
    borderColor: '#818cf8',
    borderRadius: 8,
    padding: 16,
    justifyContent: 'center',
  },
  zoneTagRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 6,
  },
  zoneTagRole: {
    fontSize: 9,
    fontWeight: '700',
    color: '#ffffff',
    backgroundColor: '#3b82f6',
    paddingVertical: 2,
    paddingHorizontal: 6,
    borderRadius: 4,
  },
  zoneDimTag: {
    fontSize: 10,
    color: '#94a3b8',
    fontWeight: '500',
  },
  zoneTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#f8fafc',
    marginBottom: 4,
  },
  zoneSub: {
    fontSize: 11,
    color: '#94a3b8',
  },
  cornerContainer: {
    flex: 1,
    position: 'relative',
  },
  cornerMainApp: {
    flex: 1,
    backgroundColor: 'rgba(99, 102, 241, 0.12)',
    borderWidth: 1.5,
    borderColor: '#818cf8',
    borderRadius: 8,
    padding: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  cornerOverlayWidget: {
    position: 'absolute',
    width: 220,
    height: 124,
    backgroundColor: 'rgba(15, 23, 42, 0.92)',
    borderWidth: 2,
    borderColor: '#0284c7',
    borderRadius: 8,
    padding: 12,
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.5,
    shadowRadius: 10,
    elevation: 8,
  },
  monitorFooter: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    backgroundColor: '#121217',
    borderTopWidth: 1,
    borderTopColor: '#1d1d24',
    alignItems: 'center',
  },
  monitorFooterText: {
    fontSize: 11,
    color: '#6b7280',
    fontFamily: 'monospace',
  },
});