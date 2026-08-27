from __future__ import annotations

import shutil
import sys
from pathlib import Path


INDEX_TSX = r'''import { useState, useEffect } from 'react';
import { MacOSProvider } from '@/contexts/MacOSContext';
import { Desktop } from '@/components/macos/Desktop';
import { LockScreen } from '@/components/macos/LockScreen';
import { SleepScreen } from '@/components/macos/SleepScreen';
import { RestartScreen } from '@/components/macos/RestartScreen';
import { HelloIntro } from '@/components/macos/HelloIntro';
import { TechnologiesApp } from '@/components/apps/TechnologiesApp';
import { JourneyApp } from '@/components/apps/JourneyApp';
import { ContactApp } from '@/components/apps/ContactApp';
import { GitHubApp } from '@/components/apps/GitHubApp';
import { LinkedInApp } from '@/components/apps/LinkedInApp';
import { SettingsApp } from '@/components/apps/SettingsApp';
import { FinderApp } from '@/components/apps/FinderApp';
import { LaunchpadApp } from '@/components/apps/LaunchpadApp';
import { TerminalApp } from '@/components/apps/TerminalApp';
import { NotesApp } from '@/components/apps/NotesApp';
import { SafariApp } from '@/components/apps/SafariApp';
import { AppStoreApp } from '@/components/apps/AppStoreApp';
import { CalculatorApp } from '@/components/apps/CalculatorApp';
import { GoogleApp } from '@/components/apps/GoogleApp';
import { CalendarApp } from '@/components/apps/CalendarApp';
import { AppleMusicApp } from '@/components/apps/AppleMusicApp';
import { MapsApp } from '@/components/apps/MapsApp';
import { AppleOSBoot, type AppleOSMode } from '@/components/appleos/AppleOSBoot';
import { PearisticMobile } from '@/components/appleos/PearisticMobile';
import { AppConfig } from '@/types/macos';

const apps: AppConfig[] = [
  { id: 'finder', name: 'Finder', icon: '📁', component: FinderApp, defaultSize: { width: 930, height: 600 }, chromeMode: 'integrated' },
  { id: 'launchpad', name: 'Launchpad', icon: '🚀', component: LaunchpadApp, defaultSize: { width: 1000, height: 700 } },
  { id: 'terminal', name: 'Terminal', icon: '💻', component: TerminalApp, defaultSize: { width: 870, height: 775 }, chromeMode: 'transparent', chromeColor: '#1d1f21' },
  { id: 'journey', name: 'Journey', icon: '🚀', component: JourneyApp, defaultSize: { width: 1200, height: 825 }, chromeMode: 'integrated' },
  { id: 'notes', name: 'Notes', icon: '📒', component: NotesApp, defaultSize: { width: 1100, height: 780 }, chromeMode: 'integrated' },
  { id: 'maps', name: 'Maps', icon: '🗺️', component: MapsApp, defaultSize: { width: 1150, height: 790 }, chromeMode: 'integrated' },
  { id: 'calendar', name: 'Calendar', icon: '📅', component: CalendarApp, defaultSize: { width: 1300, height: 900 }, chromeMode: 'integrated' },
  { id: 'technologies', name: 'VS Code', icon: '⚙️', component: TechnologiesApp, defaultSize: { width: 1370, height: 950 }, chromeMode: 'transparent', chromeColor: '#3B3B3B' },
  { id: 'safari', name: 'Safari', icon: '🧭', component: SafariApp, defaultSize: { width: 1580, height: 1070 }, chromeMode: 'integrated' },
  { id: 'google', name: 'Google', icon: 'G', component: GoogleApp, defaultSize: { width: 1580, height: 1070 }, chromeMode: 'integrated' },
  { id: 'applemusic', name: 'Music', icon: '🎵', component: AppleMusicApp, defaultSize: { width: 1320, height: 950 }, chromeMode: 'integrated' },
  { id: 'github', name: 'GitHub', icon: '🐙', component: GitHubApp, defaultSize: { width: 1070, height: 930 }, chromeMode: 'integrated' },
  { id: 'linkedin', name: 'LinkedIn', icon: '💼', component: LinkedInApp, defaultSize: { width: 1080, height: 880 }, chromeMode: 'integrated' },
  { id: 'contact', name: 'Contact', icon: '✉️', component: ContactApp, defaultSize: { width: 850, height: 750 }, chromeMode: 'integrated' },
  { id: 'calculator', name: 'Calculator', icon: '🧮', component: CalculatorApp, defaultSize: { width: 300, height: 520 }, nonResizable: true, noMaximize: true, chromeMode: 'integrated' },
  { id: 'appstore', name: 'App Store', icon: '🛍️', component: AppStoreApp, defaultSize: { width: 1100, height: 680 }, chromeMode: 'integrated' },
  { id: 'settings', name: 'Settings', icon: '⚙️', component: SettingsApp, defaultSize: { width: 1000, height: 790 }, chromeMode: 'integrated' },
];

const VISITED_KEY = 'thanasos-visited-v1';

const Index = () => {
  const [mode, setMode] = useState<AppleOSMode | null>(null);
  const [showHello, setShowHello] = useState(() => {
    if (typeof window === 'undefined') return false;
    return !sessionStorage.getItem(VISITED_KEY);
  });
  const [locked, setLocked] = useState(true);
  const [relocking, setRelocking] = useState(false);
  const [sleeping, setSleeping] = useState(false);
  const [restarting, setRestarting] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem('macos-settings');
      if (saved && JSON.parse(saved).theme) return;
    } catch { /* ignore */ }
    const prefersDark = window.matchMedia?.('(prefers-color-scheme: dark)').matches;
    const cur = JSON.parse(localStorage.getItem('macos-settings') || '{}');
    localStorage.setItem('macos-settings', JSON.stringify({ ...cur, theme: prefersDark ? 'dark' : 'light' }));
    document.documentElement.classList.toggle('dark', prefersDark);
  }, []);

  useEffect(() => {
    const onLock = () => {
      setRelocking(true);
      setLocked(true);
      setTimeout(() => setRelocking(false), 750);
    };
    const onSleep = () => setSleeping(true);
    const onRestart = () => {
      setRestarting(true);
      setTimeout(() => {
        setRestarting(false);
        setLocked(true);
      }, 10000);
    };
    const onSwitchMode = () => setMode(null);
    window.addEventListener('os:lock', onLock);
    window.addEventListener('os:sleep', onSleep);
    window.addEventListener('os:restart', onRestart);
    window.addEventListener('appleos:switch-mode', onSwitchMode);
    return () => {
      window.removeEventListener('os:lock', onLock);
      window.removeEventListener('os:sleep', onSleep);
      window.removeEventListener('os:restart', onRestart);
      window.removeEventListener('appleos:switch-mode', onSwitchMode);
    };
  }, []);

  const finishHello = () => {
    sessionStorage.setItem(VISITED_KEY, '1');
    setShowHello(false);
  };

  if (mode === null) return <AppleOSBoot onChoose={setMode} />;
  if (mode === 'mobile') return <PearisticMobile onSwitchMode={() => setMode(null)} />;

  return (
    <MacOSProvider apps={apps}>
      <Desktop />
      {locked && <LockScreen onUnlock={() => setLocked(false)} enterFromTop={relocking} />}
      {sleeping && <SleepScreen onWake={() => setSleeping(false)} />}
      {restarting && <RestartScreen onDone={() => { /* handled by timeout */ }} durationMs={10000} />}
      {showHello && <HelloIntro onDone={finishHello} />}
    </MacOSProvider>
  );
};

export default Index;
'''

BOOT_TSX = r'''import { useState } from 'react';

export type AppleOSMode = 'desktop' | 'mobile';

export const AppleOSBoot = ({ onChoose }: { onChoose: (mode: AppleOSMode) => void }) => {
  const [fullscreenBlocked, setFullscreenBlocked] = useState(false);

  const choose = async (mode: AppleOSMode) => {
    try {
      if (!document.fullscreenElement && document.documentElement.requestFullscreen) {
        await document.documentElement.requestFullscreen({ navigationUI: 'hide' });
      }
      setFullscreenBlocked(false);
    } catch {
      setFullscreenBlocked(true);
    } finally {
      onChoose(mode);
    }
  };

  return (
    <div className="fixed inset-0 z-[99999] grid place-items-center bg-[radial-gradient(circle_at_50%_35%,#25262d_0,#0b0c10_52%,#030304_100%)] text-white">
      <div className="w-[min(820px,calc(100vw-34px))] rounded-[30px] border border-white/15 bg-zinc-900/60 p-8 shadow-2xl backdrop-blur-3xl">
        <div className="text-center text-3xl font-semibold">Choose your AppleOS interface</div>
        <div className="mx-auto mt-2 max-w-xl text-center text-sm text-zinc-400">
          Desktop is the real ThanasOS source. Mobile is the real PearisticOS build.
        </div>
        <div className="mt-7 grid gap-4 md:grid-cols-2">
          <button onClick={() => void choose('desktop')} className="flex h-52 flex-col justify-between rounded-3xl border border-white/15 bg-white/10 p-6 text-left transition hover:-translate-y-1 hover:bg-white/15">
            <span className="text-6xl">🖥️</span>
            <span><b className="text-2xl">Desktop — ThanasOS</b><small className="mt-1 block text-zinc-400">Original Desktop, windows, Dock magnification, menu bar, Control Center, Spotlight, apps and animations.</small></span>
          </button>
          <button onClick={() => void choose('mobile')} className="flex h-52 flex-col justify-between rounded-3xl border border-white/15 bg-white/10 p-6 text-left transition hover:-translate-y-1 hover:bg-white/15">
            <span className="text-6xl">📱</span>
            <span><b className="text-2xl">Mobile — PearisticOS</b><small className="mt-1 block text-zinc-400">Your PearisticOS index.html runs directly as the mobile base.</small></span>
          </button>
        </div>
        {fullscreenBlocked && <div className="mt-4 text-center text-xs text-zinc-400">Fullscreen was blocked by the browser. Press F11 if you want browser fullscreen.</div>}
      </div>
    </div>
  );
};
'''

MOBILE_TSX = r'''import pearisticHtml from '@/appleos/pearistic.html?raw';

export const PearisticMobile = ({ onSwitchMode }: { onSwitchMode: () => void }) => (
  <div className="fixed inset-0 overflow-hidden bg-black">
    <iframe
      title="PearisticOS Mobile"
      srcDoc={pearisticHtml}
      className="absolute inset-0 h-full w-full border-0 bg-black"
      allow="fullscreen; autoplay; clipboard-read; clipboard-write; camera; microphone; geolocation"
    />
    <button
      type="button"
      onClick={onSwitchMode}
      className="fixed left-1 top-1/2 z-[999999] -translate-y-1/2 rounded-r-xl border border-l-0 border-white/20 bg-black/25 px-1.5 py-4 text-[10px] text-white/40 backdrop-blur transition hover:bg-black/70 hover:text-white"
      aria-label="Switch AppleOS interface"
      title="Switch interface"
    >
      ◀
    </button>
  </div>
);
'''

VITE_CONFIG = r'''import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

export default defineConfig(() => ({
  base: './',
  server: {
    host: "::",
    port: 8080,
  },
  plugins: [react()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    assetsInlineLimit: 500_000_000,
    cssCodeSplit: false,
    sourcemap: false,
    rollupOptions: {
      output: {
        inlineDynamicImports: true,
      },
    },
  },
}));
'''


def patch_settings(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace("Thanas R", "Doruk")
    text = text.replace("thanas5.rd@gmail.com", "AppleOS Account")
    text = text.replace("Thanas's", "Doruk's")
    text = text.replace("THANAS-LAPTOP", "DORUK-LAPTOP")

    sidebar_photo = '<img src={profilePhoto} alt="Doruk" className="w-10 h-10 rounded-full object-cover ring-1 ring-black/10 dark:ring-white/10" />'
    sidebar_avatar = '<div aria-label="Doruk" className="w-10 h-10 rounded-full grid place-items-center bg-gradient-to-br from-blue-500 to-violet-600 text-white text-lg font-semibold ring-1 ring-black/10 dark:ring-white/10">D</div>'
    pane_photo = '<img src={profilePhoto} alt="Doruk" className="w-20 h-20 rounded-full object-cover ring-1 ring-black/10 dark:ring-white/10 mb-3" />'
    pane_avatar = '<div aria-label="Doruk" className="w-20 h-20 rounded-full grid place-items-center bg-gradient-to-br from-blue-500 to-violet-600 text-white text-3xl font-semibold ring-1 ring-black/10 dark:ring-white/10 mb-3">D</div>'

    if sidebar_photo not in text:
        raise RuntimeError("Could not locate ThanasOS sidebar account photo markup")
    if pane_photo not in text:
        raise RuntimeError("Could not locate ThanasOS account pane photo markup")

    text = text.replace(sidebar_photo, sidebar_avatar)
    text = text.replace(pane_photo, pane_avatar)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: patch.py <thanasos-root> <pearistic-index.html>")

    root = Path(sys.argv[1]).resolve()
    pearistic = Path(sys.argv[2]).resolve()
    if not pearistic.exists():
        raise FileNotFoundError(pearistic)

    components = root / "src/components/appleos"
    payload_dir = root / "src/appleos"
    components.mkdir(parents=True, exist_ok=True)
    payload_dir.mkdir(parents=True, exist_ok=True)

    (root / "src/pages/Index.tsx").write_text(INDEX_TSX, encoding="utf-8")
    (components / "AppleOSBoot.tsx").write_text(BOOT_TSX, encoding="utf-8")
    (components / "PearisticMobile.tsx").write_text(MOBILE_TSX, encoding="utf-8")
    shutil.copy2(pearistic, payload_dir / "pearistic.html")
    (root / "vite.config.ts").write_text(VITE_CONFIG, encoding="utf-8")
    patch_settings(root / "src/components/apps/SettingsApp.tsx")

    print("Patched real ThanasOS with AppleOS boot + real PearisticOS mobile + Doruk account")


if __name__ == "__main__":
    main()
