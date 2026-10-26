const express = require("express");
const { z } = require("zod");
const prisma = require("../config/prisma");
const asyncHandler = require("../utils/asyncHandler");

const router = express.Router();

const scenarioSchema = z.object({
  name: z.string().trim().min(1).max(160),
  description: z.string().max(2000).optional().nullable(),
  assumptions: z.string().max(5000).optional().nullable(),
  inputs: z.record(z.unknown()),
  results: z.record(z.unknown()).optional().nullable(),
});

router.post("/", asyncHandler(async (req, res) => {
  const parsed = scenarioSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: "Invalid scenario payload.", details: parsed.error.flatten() });

  const scenario = await prisma.scenario.create({
    data: { ...parsed.data, userId: req.user.id },
  });
  return res.status(201).json({ scenario });
}));

router.get("/", asyncHandler(async (req, res) => {
  const scenarios = await prisma.scenario.findMany({
    where: { userId: req.user.id },
    orderBy: { updatedAt: "desc" },
  });
  return res.json({ scenarios });
}));

router.get("/:id", asyncHandler(async (req, res) => {
  const scenario = await prisma.scenario.findFirst({
    where: { id: req.params.id, userId: req.user.id },
  });
  if (!scenario) return res.status(404).json({ error: "Scenario not found." });
  return res.json({ scenario });
}));

router.patch("/:id", asyncHandler(async (req, res) => {
  const parsed = scenarioSchema.partial().safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: "Invalid scenario update.", details: parsed.error.flatten() });
  if (!Object.keys(parsed.data).length) return res.status(400).json({ error: "Provide at least one field to update." });

  const existing = await prisma.scenario.findFirst({
    where: { id: req.params.id, userId: req.user.id },
    select: { id: true },
  });
  if (!existing) return res.status(404).json({ error: "Scenario not found." });

  const scenario = await prisma.scenario.update({
    where: { id: existing.id },
    data: parsed.data,
  });
  return res.json({ scenario });
}));

router.delete("/:id", asyncHandler(async (req, res) => {
  const result = await prisma.scenario.deleteMany({
    where: { id: req.params.id, userId: req.user.id },
  });
  if (!result.count) return res.status(404).json({ error: "Scenario not found." });
  return res.status(204).send();
}));

module.exports = router;
