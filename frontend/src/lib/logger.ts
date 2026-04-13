import pino from "pino";

// Use pino-pretty only in development for readable console logs
const isDev = process.env.NODE_ENV !== "production";

export const logger = pino({
  level: process.env.LOG_LEVEL || "info",
  browser: {
    asObject: true,
  },
  ...(isDev && typeof window === "undefined" && {
    transport: {
      target: "pino-pretty",
      options: {
        colorize: true,
        translateTime: "SYS:standard",
        ignore: "pid,hostname",
      },
    },
  }),
});
