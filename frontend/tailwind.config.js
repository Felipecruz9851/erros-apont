/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        lider: {
          canvas: "#F8F8F8",
          card: "#FFFFFF",
          subtle: "#F0F0F0",
          border: "#E0E0E0",
          divider: "#EBEBEB",
          primary: "#1A1A1A",
          secondary: "#666666",
          tertiary: "#999999",
          wood: "#8B5A2B",
          woodDark: "#6B4423",
          woodLight: "#A67242",
          danger: "#9E2A2B",
          dangerLight: "#FDF2F2",
          warning: "#B07D1E",
          warningLight: "#FEF9EC",
          success: "#2D6A4F",
          successLight: "#F0FDF4",
        },
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', '-apple-system', 'sans-serif'],
      },
      borderRadius: {
        'sm': '2px',
        'DEFAULT': '3px',
        'md': '4px',
        'lg': '6px',
      },
      boxShadow: {
        'subtle': '0 1px 3px rgba(0, 0, 0, 0.04)',
        'card': '0 2px 4px rgba(0, 0, 0, 0.03)',
        'modal': '0 8px 24px rgba(0, 0, 0, 0.06)',
      },
    },
  },
  plugins: [],
}
