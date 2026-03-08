const express = require("express");
const router = express.Router();
const { 
  suggestInitials,
  updateInitials,
  updateInstitutionType,
  getProfile
} = require("../controllers/institutionController");
const { protectInstitution } = require("../middleware/authMiddleware");


// All routes require institution authentication
router.get("/profile", protectInstitution, getProfile);
router.get("/initials/suggest", protectInstitution, suggestInitials);
router.patch("/initials", protectInstitution, updateInitials);
router.patch("/type", protectInstitution, updateInstitutionType);

module.exports = router;
