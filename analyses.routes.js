const express = require("express");
const { z } = require("zod");
const prisma = require("../config/prisma");
const asyncHandler = require("../utils/asyncHandler");

const router = express.Router();

const analysisSchema = z.object({
  title: z.string().trim().min(1).max(160),
  fileId: z.string().optional().nullable(),
  summary: z.string().max(5000).optional().nullable(),
  results: z.record(z.unknown()),
});

router.post("/", asyncHandler(async (req, res) => {
  const parsed = analysisSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: "Invalid analysis payload.", details: parsed.error.flatten() });

  const data = { ...parsed.data, userId: req.user.id };
  if (data.fileId) {
    const file = await prisma.uploadedFile.findFirst({ where: { id: data.fileId, userId: req.user.id } });
    if (!file) return res.status(400).json({ error: "fileId does not belong to your account." });
  }

  const analysis = await prisma.analysisHistory.create({ data });
  return res.status(201).json({ analysis });
}));

router.get("/", asyncHandler(async (req, res) => {
  const analyses = await prisma.analysisHistory.findMany({
    where: { userId: req.user.id },
    orderBy: { createdAt: "desc" },
    include: { file: { select: { id: true, filename: true, fileType: true } } },
  });
  return res.json({ analyses });
}));

router.get("/:id", asyncHandler(async (req, res) => {
  const analysis = await prisma.analysisHistory.findFirst({
    where: { id: req.params.id, userId: req.user.id },
    include: { file: { select: { id: true, filename: true, fileType: true } } },
  });
  if (!analysis) return res.status(404).json({ error: "Analysis not found." });
  return res.json({ analysis });
}));

router.delete("/:id", asyncHandler(async (req, res) => {
  const result = await prisma.analysisHistory.deleteMany({
    where: { id: req.params.id, userId: req.user.id },
  });
  if (!result.count) return res.status(404).json({ error: "Analysis not found." });
  return res.status(204).send();
}));

module.exports = router;
