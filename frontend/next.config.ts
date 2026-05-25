import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  // 静态导出时禁用图片优化（需要 Node.js 服务端）
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
