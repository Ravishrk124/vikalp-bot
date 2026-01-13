/** @type {import('next').NextConfig} */
const nextConfig = {
    // Enable standalone output for optimized Vercel deployment
    output: 'standalone',

    // Configure image optimization
    images: {
        unoptimized: true, // Use unoptimized for simpler deployment
    },

    // Environment variables available at build time
    env: {
        NEXT_PUBLIC_BACKEND_ORIGIN: process.env.NEXT_PUBLIC_BACKEND_ORIGIN,
    },
};

export default nextConfig;
