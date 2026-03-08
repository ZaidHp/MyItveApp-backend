const PromoCode = require("../models/PromoCode");
const PublicCode = require("../models/PublicCode");
const Institution = require("../models/Institution");
const Classroom = require("../models/Classroom");

// Class levels for schools (KG to 10)
const SCHOOL_CLASS_LEVELS = ['KG', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'];

// Programs for colleges
const COLLEGE_PROGRAMS = ['PreMed', 'PreEng', 'Commerce', 'ALevels', 'OLevels'];

// Donor types
const DONOR_TYPES = ['Gold', 'Silver', 'Bronze', 'Platinum'];

const getCurrentBatchYear = () => {
  return new Date().getFullYear().toString().slice(-2);
};

const generateUniqueCode = () => {
  return Math.random().toString(36).substring(2, 8).toUpperCase();
};

// generate promo codes for an institution
const generateInstitutionPromoCodes = async (req, res) => {
  try {
    const institutionId = req.school._id;
    
    const institution = await Institution.findById(institutionId);
    if (!institution) {
      return res.status(404).json({ 
        success: false, 
        message: "Institution not found" 
      });
    }

    const institutionType = institution.user_type;
    const initials = institution.initials;
    
    if (!institutionType || !['school', 'college'].includes(institutionType)) {
      return res.status(400).json({ 
        success: false, 
        message: "Institution type not set. Please update your profile with type 'school' or 'college'." 
      });
    }

    if (!initials) {
      return res.status(400).json({ 
        success: false, 
        message: "Institution initials not set. Please update your profile with initials first." 
      });
    }

    const batchYear = getCurrentBatchYear();
    const promoType = institutionType; 
    const defaultSection = 'A'; // Default section for classrooms
    
    const classLevels = promoType === 'school' ? SCHOOL_CLASS_LEVELS : COLLEGE_PROGRAMS;
    
    /*
    the generated and exisiting are here because of a reason,
    if we generate the promo code and then check if it exists, 
    we might end up with duplicates if the same initials and 
    batch year are used by another institution. or if the same institution 
    tries to generate again without changing initials or batch year,
    it will create duplicates. and if classroom already exists we can 
    link the promo code to that classroom instead of creating a new one,
    */
    const generatedItems = [];
    const existingItems = [];

    for (const classLevel of classLevels) {
      const promoCode = `${initials.toUpperCase()}-${classLevel}-${batchYear}`;
      
      const classCode = `${initials.toUpperCase()}${classLevel}${defaultSection}`;
      
      const existingPromoCode = await PromoCode.findOne({ code: promoCode });
      
      if (existingPromoCode) {
        const existingClassroom = await Classroom.findById(existingPromoCode.classroomId);
        existingItems.push({
          promoCode: existingPromoCode.code,
          classLevel: existingPromoCode.classLevel,
          isActive: existingPromoCode.isActive,
          classroom: existingClassroom ? {
            classCode: existingClassroom.classCode,
            className: existingClassroom.className,
            section: existingClassroom.section
          } : null
        });
      } else {
        let classroom = await Classroom.findOne({ classCode });
        if (!classroom) {
          classroom = await Classroom.create({
            schoolId: institutionId,
            className: classLevel,
            section: defaultSection,
            schoolInitials: initials.toUpperCase(),
            classCode: classCode,
            students: []
          });
        }
        const newPromoCode = await PromoCode.create({
          code: promoCode,
          institutionId: institutionId,
          classroomId: classroom._id,
          promoType: promoType,
          classLevel: classLevel,
          batchYear: batchYear,
          isActive: true,
          usageCount: 0
        });
        
        generatedItems.push({
          promoCode: newPromoCode.code,
          classLevel: newPromoCode.classLevel,
          isActive: newPromoCode.isActive,
          classroom: {
            id: classroom._id,
            classCode: classroom.classCode,
            className: classroom.className,
            section: classroom.section
          }
        });
      }
    }

    return res.status(201).json({
      success: true,
      message: `Promo codes and classrooms generated for ${promoType}`,
      institutionType: promoType,
      initials: initials.toUpperCase(),
      batchYear,
      totalGenerated: generatedItems.length,
      alreadyExisted: existingItems.length,
      generated: generatedItems,
      existing: existingItems
    });

  } catch (error) {
    console.error("Error generating institution promo codes:", error);
    return res.status(500).json({ 
      success: false, 
      message: "Server error while generating promo codes",
      error: error.message 
    });
  }
};


// general public code generation
// Format: GP-BATCHYEAR-xxxxxx
const generateGeneralPublicCode = async (req, res) => {
  try {
    const batchYear = getCurrentBatchYear();
    const uniqueCode = generateUniqueCode();
    const code = `GP-${batchYear}-${uniqueCode}`;

    const newPublicCode = await PublicCode.create({
      code,
      codeType: 'general_public',
      donorType: null,
      batchYear,
      isActive: true,
      usageCount: 0
    });

    return res.status(201).json({
      success: true,
      message: "General public code generated successfully",
      publicCode: {
        id: newPublicCode._id,
        code: newPublicCode.code,
        codeType: newPublicCode.codeType,
        batchYear: newPublicCode.batchYear,
        isActive: newPublicCode.isActive
      }
    });

  } catch (error) {
    console.error("Error generating general public code:", error);
    return res.status(500).json({ 
      success: false, 
      message: "Server error while generating public code",
      error: error.message 
    });
  }
};

// donor code generation
// Format: DN-DONORTYPE-BATCHYEAR-xxxxxx
const generateDonorCode = async (req, res) => {
  try {
    const { donorType } = req.body;
    
    if (!donorType || !DONOR_TYPES.includes(donorType)) {
      return res.status(400).json({ 
        success: false, 
        message: `Invalid donor type. Must be one of: ${DONOR_TYPES.join(', ')}` 
      });
    }

    const batchYear = getCurrentBatchYear();
    const uniqueCode = generateUniqueCode();
    const code = `DN-${donorType}-${batchYear}-${uniqueCode}`;

    const newPublicCode = await PublicCode.create({
      code,
      codeType: 'donor',
      donorType: donorType,
      batchYear,
      isActive: true,
      usageCount: 0
    });

    return res.status(201).json({
      success: true,
      message: "Donor code generated successfully",
      publicCode: {
        id: newPublicCode._id,
        code: newPublicCode.code,
        codeType: newPublicCode.codeType,
        donorType: newPublicCode.donorType,
        batchYear: newPublicCode.batchYear,
        isActive: newPublicCode.isActive
      }
    });

  } catch (error) {
    console.error("Error generating donor code:", error);
    return res.status(500).json({ 
      success: false, 
      message: "Server error while generating donor code",
      error: error.message 
    });
  }
};


// validation promo codes as per function nmae.
const validatePromoCode = async (req, res) => {
  try {
    const { code } = req.params;
    const upperCode = code.toUpperCase();
    
    let promoCode = await PromoCode.findOne({ code: upperCode })
      .populate('institutionId', 'institute_name user_type')
      .populate('classroomId', 'classCode className section');

    if (promoCode) {
      if (!promoCode.isActive) {
        return res.status(400).json({ 
          success: false, 
          valid: false,
          message: "Promo code is no longer active" 
        });
      }

      return res.status(200).json({
        success: true,
        valid: true,
        message: "Promo code is valid",
        codeType: "institution",
        promoCode: {
          code: promoCode.code,
          promoType: promoCode.promoType,
          classLevel: promoCode.classLevel,
          batchYear: promoCode.batchYear,
          usageCount: promoCode.usageCount,
          institution: promoCode.institutionId ? {
            name: promoCode.institutionId.institute_name,
            type: promoCode.institutionId.user_type
          } : null,
          classroom: promoCode.classroomId ? {
            classCode: promoCode.classroomId.classCode,
            className: promoCode.classroomId.className,
            section: promoCode.classroomId.section
          } : null
        }
      });
    }

    const publicCode = await PublicCode.findOne({ code: upperCode });

    if (publicCode) {
      if (!publicCode.isActive) {
        return res.status(400).json({ 
          success: false, 
          valid: false,
          message: "Code is no longer active" 
        });
      }

      return res.status(200).json({
        success: true,
        valid: true,
        message: "Code is valid",
        codeType: publicCode.codeType,
        publicCode: {
          code: publicCode.code,
          codeType: publicCode.codeType,
          donorType: publicCode.donorType,
          batchYear: publicCode.batchYear,
          usageCount: publicCode.usageCount
        }
      });
    }

    return res.status(404).json({ 
      success: false, 
      valid: false,
      message: "Code not found" 
    });

  } catch (error) {
    console.error("Error validating code:", error);
    return res.status(500).json({ 
      success: false, 
      message: "Server error while validating code",
      error: error.message 
    });
  }
};

// get promo codes for an institution
const getInstitutionPromoCodes = async (req, res) => {
  try {
    const institutionId = req.school._id;
    
    const promoCodes = await PromoCode.find({ institutionId })
      .sort({ classLevel: 1, createdAt: -1 });

    return res.status(200).json({
      success: true,
      count: promoCodes.length,
      promoCodes: promoCodes.map(pc => ({
        id: pc._id,
        code: pc.code,
        promoType: pc.promoType,
        classLevel: pc.classLevel,
        batchYear: pc.batchYear,
        isActive: pc.isActive,
        usageCount: pc.usageCount,
        createdAt: pc.createdAt
      }))
    });

  } catch (error) {
    console.error("Error fetching institution promo codes:", error);
    return res.status(500).json({ 
      success: false, 
      message: "Server error while fetching promo codes",
      error: error.message 
    });
  }
};


// Get all promo codes 
const getAllPromoCodes = async (req, res) => {
  try {
    const { promoType, isActive } = req.query;
    
    const filter = {};
    if (promoType) filter.promoType = promoType;
    if (isActive !== undefined) filter.isActive = isActive === 'true';

    const promoCodes = await PromoCode.find(filter)
      .populate('institutionId', 'institute_name user_type initials')
      .populate('classroomId', 'classCode className section')
      .sort({ createdAt: -1 });

    return res.status(200).json({
      success: true,
      count: promoCodes.length,
      promoCodes: promoCodes.map(pc => ({
        id: pc._id,
        code: pc.code,
        promoType: pc.promoType,
        classLevel: pc.classLevel,
        batchYear: pc.batchYear,
        isActive: pc.isActive,
        usageCount: pc.usageCount,
        institution: pc.institutionId ? {
          id: pc.institutionId._id,
          name: pc.institutionId.institute_name,
          type: pc.institutionId.user_type,
          initials: pc.institutionId.initials
        } : null,
        classroom: pc.classroomId ? {
          classCode: pc.classroomId.classCode,
          className: pc.classroomId.className,
          section: pc.classroomId.section
        } : null,
        createdAt: pc.createdAt
      }))
    });

  } catch (error) {
    console.error("Error fetching all promo codes:", error);
    return res.status(500).json({ 
      success: false, 
      message: "Server error while fetching promo codes",
      error: error.message 
    });
  }
};


// Return all public codes.
const getAllPublicCodes = async (req, res) => {
  try {
    const { codeType, isActive } = req.query;
    
    const filter = {};
    if (codeType) filter.codeType = codeType;
    if (isActive !== undefined) filter.isActive = isActive === 'true';

    const publicCodes = await PublicCode.find(filter)
      .sort({ createdAt: -1 });

    return res.status(200).json({
      success: true,
      count: publicCodes.length,
      publicCodes: publicCodes.map(pc => ({
        id: pc._id,
        code: pc.code,
        codeType: pc.codeType,
        donorType: pc.donorType,
        batchYear: pc.batchYear,
        isActive: pc.isActive,
        usageCount: pc.usageCount,
        createdAt: pc.createdAt
      }))
    });

  } catch (error) {
    console.error("Error fetching public codes:", error);
    return res.status(500).json({ 
      success: false, 
      message: "Server error while fetching public codes",
      error: error.message 
    });
  }
};

// untested 
const deactivatePromoCode = async (req, res) => {
  try {
    const { code } = req.params;
    
    const promoCode = await PromoCode.findOneAndUpdate(
      { code: code.toUpperCase() },
      { isActive: false },
      { new: true }
    );

    if (!promoCode) {
      return res.status(404).json({ 
        success: false, 
        message: "Promo code not found" 
      });
    }

    return res.status(200).json({
      success: true,
      message: "Promo code deactivated successfully",
      promoCode: {
        code: promoCode.code,
        isActive: promoCode.isActive
      }
    });

  } catch (error) {
    console.error("Error deactivating promo code:", error);
    return res.status(500).json({ 
      success: false, 
      message: "Server error while deactivating promo code",
      error: error.message 
    });
  }
};

// untested 
const usePromoCode = async (req, res) => {
  try {
    const { code } = req.params;
    const upperCode = code.toUpperCase();
    
    let promoCode = await PromoCode.findOne({ code: upperCode });

    if (promoCode) {
      if (!promoCode.isActive) {
        return res.status(400).json({ 
          success: false, 
          message: "Promo code is no longer active" 
        });
      }

      promoCode.usageCount += 1;
      await promoCode.save();

      return res.status(200).json({
        success: true,
        message: "Promo code used successfully",
        code: {
          code: promoCode.code,
          usageCount: promoCode.usageCount,
          codeType: "institution"
        }
      });
    }

    const publicCode = await PublicCode.findOne({ code: upperCode });

    if (publicCode) {
      if (!publicCode.isActive) {
        return res.status(400).json({ 
          success: false, 
          message: "Code is no longer active" 
        });
      }

      publicCode.usageCount += 1;
      await publicCode.save();

      return res.status(200).json({
        success: true,
        message: "Code used successfully",
        code: {
          code: publicCode.code,
          usageCount: publicCode.usageCount,
          codeType: publicCode.codeType
        }
      });
    }

    return res.status(404).json({ 
      success: false, 
      message: "Code not found" 
    });

  } catch (error) {
    console.error("Error using code:", error);
    return res.status(500).json({ 
      success: false, 
      message: "Server error while using code",
      error: error.message 
    });
  }
};

module.exports = {
  generateInstitutionPromoCodes,
  generateGeneralPublicCode,
  generateDonorCode,
  validatePromoCode,
  getInstitutionPromoCodes,
  getAllPromoCodes,
  getAllPublicCodes,
  deactivatePromoCode,
  usePromoCode
};
