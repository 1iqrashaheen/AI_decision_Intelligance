const express = require("express");
const { z } = require("zod");
const prisma = require("../config/prisma");
const asyncHandler = require("../utils/asyncHandler");

const router = express.Router();

const fileSchema = z.object({
  filename: z.string().trim().min(1).max(255),
  fileType: z.string().trim().max(100).optional(),
  fileSize: z.number().int().nonnegative().optional(),
  storagePath: z.string().trim().max(1000).optional(),
  metadata: z.record(z.unknown()).optional(),
});

// This stores file metadata only. Actual CSV/Excel upload and storage are a separate module.
router.post("/", asyncHandler(async (req, res) => {
  const parsed = fileSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: "Invalid file metadata.", details: parsed.error.flatten() });

  const file = await prisma.uploadedFile.create({
    data: { ...parsed.data, userId: req.user.id },
  });
  return res.status(201).json({ file });
}));

router.get("/", asyncHandler(async (req, res) => {
  const files = await prisma.uploadedFile.findMany({
    where: { userId: req.user.id },
    orderBy: { createdAt: "desc" },
  });
  return res.json({ files });
}));

router.get("/:id", asyncHandler(async (req, res) => {
  const file = await prisma.uploadedFile.findFirst({
    where: { id: req.params.id, userId: req.user.id },
  });
  if (!file) return res.status(404).json({ error: "File record not found." });
  return res.json({ file });
}));

module.exports = router;
