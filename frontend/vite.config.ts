import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import federation from '@originjs/vite-plugin-federation'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    federation({
      name: 'parallel_coding_app',
      filename: 'remoteEntry.js',
      // Expose components for use in Ecosystem Dashboard
      exposes: {
        './App': './src/App.tsx',
        './WorkerStatusDashboard': './src/components/WorkerStatusDashboard.tsx',
        './MetricsDashboard': './src/components/MetricsDashboard.tsx',
        './DialogueView': './src/components/DialogueView.tsx',
        './TerminalGridLayout': './src/components/TerminalGridLayout.tsx',
      },
      // Shared dependencies to avoid duplication
      shared: ['react', 'react-dom']
    })
  ],
  build: {
    modulePreload: false,
    target: 'esnext',
    minify: false,
    cssCodeSplit: false
  }
})
