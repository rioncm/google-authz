import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  return {
    plugins: [react()],
    define: {
      __BASE_URL__: JSON.stringify(env.VITE_AUTHZ_BASE_URL || 'http://localhost:8000'),
      __REQUIRED_PERMISSION__: JSON.stringify(env.VITE_REQUIRED_PERMISSION || 'inventory:read'),
    },
  }
})
