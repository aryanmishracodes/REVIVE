/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        fintech: {
          bg: "#080C14",
          sidebar: "#0D131F",
          card: "#111827",
          cardHover: "#162032",
          border: "#1F293D",
          borderLight: "#2D3B55",
          accent: "#3B82F6",
          emerald: "#10B981",
          emeraldDim: "rgba(16, 185, 129, 0.12)",
          amber: "#F59E0B",
          amberDim: "rgba(245, 158, 11, 0.12)",
          rose: "#F43F5E",
          roseDim: "rgba(244, 63, 94, 0.12)",
          indigo: "#6366F1",
          textMuted: "#94A3B8",
          textDim: "#64748B",
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        fintech: '0 4px 20px -2px rgba(0, 0, 0, 0.5), 0 0 1px 1px rgba(255, 255, 255, 0.05)',
        glow: '0 0 25px -5px rgba(59, 130, 246, 0.3)',
        emeraldGlow: '0 0 25px -5px rgba(16, 185, 129, 0.3)',
      }
    },
  },
  plugins: [],
}
