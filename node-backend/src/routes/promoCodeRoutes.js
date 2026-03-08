const express = require("express");
const router = express.Router();
const { 
  generateInstitutionPromoCodes, 
  generateGeneralPublicCode, 
  generateDonorCode,
  validatePromoCode,
  getInstitutionPromoCodes,
  getAllPromoCodes,
  getAllPublicCodes,
  deactivatePromoCode,
  usePromoCode
} = require("../controllers/promoCodeController");
const { protectInstitution, protectUser } = require("../middleware/authMiddleware");

// Institution routes 
router.post("/generate/institution", protectInstitution, generateInstitutionPromoCodes);
router.get("/institution", protectInstitution, getInstitutionPromoCodes);

// General public and donor codes 
router.post("/generate/general-public", protectUser, generateGeneralPublicCode);
router.post("/generate/donor", protectUser, generateDonorCode);

// Public routes
router.get("/validate/:code", validatePromoCode);

// Public for now - can be protected later if needed
// need clearity here
router.get("/all", protectUser, getAllPromoCodes);  // Institution promo codes
router.get("/all/public", protectUser, getAllPublicCodes);  // General public & donor codes

// not tested
router.patch("/:code/deactivate", protectUser, deactivatePromoCode);
router.post("/:code/use", usePromoCode); // Usage tracking

module.exports = router;
