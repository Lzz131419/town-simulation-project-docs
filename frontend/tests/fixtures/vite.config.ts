import config from "../../vite.config";

// Dedicated browser-test frontend; the regular Vite config has no reset proxy.
export default {
  ...config,
  server: {
    ...config.server,
    port: 5174,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8010",
        ws: true,
        changeOrigin: false,
      },
      "/__test": { target: "http://127.0.0.1:8010" },
    },
  },
};
