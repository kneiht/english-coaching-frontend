import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import viteReact from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { cpSync } from 'node:fs'

import { tanstackRouter } from '@tanstack/router-plugin/vite'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    tanstackRouter({ autoCodeSplitting: true }),
    viteReact(),
    tailwindcss(),
    {
      name: 'copy-mock-data',
      closeBundle() {
        try {
          cpSync(
            resolve(__dirname, 'src/mock-data'),
            resolve(__dirname, 'dist/src/mock-data'),
            { recursive: true }
          )
          console.log('✓ Successfully copied src/mock-data to dist/src/mock-data')
        } catch (err) {
          console.error('Failed to copy mock data to dist:', err)
        }
      }
    }
  ],
  // test: {
  //   globals: true,
  //   environment: 'jsdom',
  // },
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
})
