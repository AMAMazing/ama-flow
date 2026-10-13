export const PRODUCT_INFO = {
  name: "WindowZones",
  tagline: "Intelligent Desktop Geometry & Virtual Tiling Orchestrator",
  subtagline: "Commercial closed-source window management utility built for power users, developers, and ultrawide setups. Frictionless 14-day reverse trial with zero subscriptions required.",
  status: "COMING SOON — CLOSED SOURCE COMMERCIAL RELEASE",
  releaseTarget: "Windows 10 / 11 Native Desktop",
};

export const PRICING_TIERS = [
  {
    id: "personal",
    name: "Personal License",
    badge: "Most Popular",
    price: "$24",
    billing: "One-Time Perpetual License",
    highlight: true,
    description: "Full lifetime ownership of the purchased version. No recurring monthly fees or mandatory subscriptions.",
    features: [
      "Perpetual fallback lifetime license",
      "1 Full Year of free updates & new features",
      "Activate on up to 3 personal machines",
      "Unlimited custom layouts & saved presets",
      "Dynamic Multi-Monitor & Ultrawide (21:9 / 32:9) detection",
      "Chrome PiP & standalone PWA auto-aspect pinning",
      "50% renewal discount ($12/yr) after year 1, or keep current version forever",
      "100% offline Ed25519 cryptographic license verification"
    ],
    cta: "Pre-order Personal Edition"
  },
  {
    id: "commercial",
    name: "Commercial Seat",
    badge: "For Teams",
    price: "$59",
    billing: "Per Seat / One-Time",
    highlight: false,
    description: "Authorized for corporate workstations, developers, creative studios, and commercial environments.",
    features: [
      "Permitted for corporate & commercial enterprise usage",
      "Centralized license key management for IT bulk rollout",
      "Silent CLI deployment & automated registry config",
      "Priority bug fixes & direct developer SLA support",
      "All Pro multi-monitor & workspace automation features",
      "Hardware GUID machine binding control",
      "Volume discounts available for 10+ seats"
    ],
    cta: "Inquire for Team Licenses"
  },
  {
    id: "store",
    name: "Microsoft Store Edition",
    badge: "Frictionless Sandbox",
    price: "$19.99",
    billing: "Flat One-Time Purchase",
    highlight: false,
    description: "Packaged for non-technical power users who demand 1-click install through the trusted Microsoft Store.",
    features: [
      "1-Click verified installation from Microsoft Store",
      "Automatic background updates managed by Windows",
      "Isolated Windows sandbox execution",
      "Native Windows 11 Fluent Acrylic design",
      "Single PC license tied to Microsoft Account",
      "Zero installer or dependency headaches"
    ],
    cta: "Notify on Store Release"
  }
];

export const FEATURE_COMPARISON = [
  { feature: "Standard Grid & Column Snapping", free: "Yes", pro: "Yes" },
  { feature: "Global Hotkey Snapping Engine (Win+Shift+Z, Ctrl+Win+Z)", free: "Yes", pro: "Yes" },
  { feature: "Visual Desktop Overlay on Drag Modifier (Hold Ctrl)", free: "Yes", pro: "Yes" },
  { feature: "Custom Saved Layouts", free: "Max 2 Layouts", pro: "Unlimited Layouts" },
  { feature: "Multi-Monitor & Ultrawide (21:9 & 32:9) Dynamic Engine", free: "Single Monitor Only", pro: "Dynamic Multi-Monitor" },
  { feature: "Chrome Picture-in-Picture Smart Detection", free: "Basic (16:9 only)", pro: "Advanced (All Profiles)" },
  { feature: "Standalone PWA COM UIAutomation Classification", free: "Manual Only", pro: "Automatic COM Hooks" },
  { feature: "Floating Corner PiP Modes (All 4 Quadrants)", free: "Bottom-Right only", pro: "All Corners + Smart Resizing" },
  { feature: "Workspace Profiles (Coding, Media, Stock Trading)", free: "No", pro: "Yes (1-Click Switch)" },
  { feature: "Offline Cryptographic Verification (Zero Downtime)", free: "N/A", pro: "Ed25519 Public Key" }
];

export const ROADMAP_PHASES = [
  {
    phase: "Phase 1: Validated Python Win32 Engine",
    status: "Completed Prototype",
    current: true,
    points: [
      "Low-level Win32 ctypes hooks (SetWinEventHook, DwmGetWindowAttribute).",
      "Sub-pixel window margin adjustment removing invisible Windows 11 resize borders.",
      "Pure geometric tiling layout engine with 50/50 splits & custom companion sizing.",
      "UIAutomation COM integration differentiating PWAs from standard Chrome tabs."
    ]
  },
  {
    phase: "Phase 2: Hybrid Tauri v2 Architecture",
    status: "In Development",
    current: false,
    points: [
      "Decoupled web frontend styled with modern responsive components.",
      "Native Windows notification tray lifecycle with zero unwanted console windows.",
      "High-speed local JSON-RPC IPC over Windows Named Pipes.",
      "Hardware-accelerated acrylic / mica visual snapping overlay."
    ]
  },
  {
    phase: "Phase 3: Native Rust Core Production Binary",
    status: "Upcoming Production Release",
    current: false,
    points: [
      "100% elimination of Python runtime, DLLs, and interpreter overhead.",
      "Idle memory footprint slashed to 8-15 MB RAM.",
      "Cold startup time under 150 milliseconds.",
      "Standalone ~12 MB compact executable with auto-updating and code-signing."
    ]
  }
];

export const TRIAL_FLOW = [
  {
    day: "Day 0 - 14",
    title: "14-Day Reverse Trial (100% Unlocked)",
    desc: "Experience every Pro feature immediately. No credit card required, no account creation, and zero friction. Form muscle memory and build custom layouts."
  },
  {
    day: "Day 14+",
    title: "Graceful Downgrade — Never Disables Your Workflow",
    desc: "WindowZones never locks you out or bricks your windows. Core snapping remains permanently functional; upgrade only when you need unlimited profiles & multimonitor automation."
  }
];