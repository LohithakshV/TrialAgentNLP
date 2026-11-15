export default {
  poweredByHeader: false,
  devIndicators: false,
  async rewrites() { return [{ source: '/api/:path*', destination: 'http://127.0.0.1:8000/api/:path*' }]; },
  async headers() { return [{ source: '/:path*', headers: [
    { key: 'Referrer-Policy', value: 'no-referrer' },
    { key: 'X-Content-Type-Options', value: 'nosniff' },
    { key: 'X-Frame-Options', value: 'DENY' },
    { key: 'Cache-Control', value: 'no-store' }
  ] }]; }
};
