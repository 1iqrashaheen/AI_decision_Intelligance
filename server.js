require("dotenv").config();

const express = require("express");
const cors = require("cors");
const helmet = require("helmet");
const prisma = require("./config/prisma");
const { requireAuth } = require("./middleware/auth");

if (!process.env.DATABASE_URL) {
  console.error("Missing DATABASE_URL. Copy .env.example to .env and configure PostgreSQL.");
  process.exit(1);
}
if (!process.env.JWT_SECRET || process.env.JWT_SECRET.length < 32) {
  console.error("JWT_SECRET must be configured with at least 32 characters.");
  process.exit(1);
}

const app = express();
app.use(helmet());
app.use(cors({
  origin: process.env.CLIENT_ORIGIN ? process.env.CLIENT_ORIGIN.split(",").map((v) => v.trim()) : true,
}));
app.use(express.json({ limit: "1mb" }));

app.get("/api/health", async (req, res) => {
  try {
    await prisma.$queryRaw`SELECT 1`;
    return res.json({ status: "ok", database: "connected" });
  } catch {
    return res.status(503).json({ status: "error", database: "unavailable" });
  }
});

app.use("/api/auth", require("./routes/auth.routes"));
app.use("/api/files", requireAuth, require("./routes/files.routes"));
app.use("/api/analyses", requireAuth, require("./routes/analyses.routes"));
app.use("/api/scenarios", requireAuth, require("./routes/scenarios.routes"));

app.use((req, res) => res.status(404).json({ error: "Route not found." }));

app.use((err, req, res, next) => {
  if (err && err.code === "P2002") return res.status(409).json({ error: "A record with this unique value already exists." });
  console.error(err);
  return res.status(500).json({ error: "Internal server error." });
});

const port = Number(process.env.PORT || 4000);
const server = app.listen(port, () => console.log(`API listening on http://localhost:${port}`));

async function shutdown() {
  server.close(async () => {
    await prisma.$disconnect();
    process.exit(0);
  });
}
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
