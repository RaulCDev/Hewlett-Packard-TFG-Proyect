/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // This project uses the Pages Router. Disabling the unused experimental App
  // Router also avoids Next 13.4's render-worker proxy on slim containers.
  experimental: {
    appDir: false,
  },
}

module.exports = nextConfig
