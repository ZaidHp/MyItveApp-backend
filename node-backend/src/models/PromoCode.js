const mongoose = require("mongoose");

const promoCodeSchema = new mongoose.Schema({
  code: { type: String, required: true, unique: true },
  institutionId: { 
    type: mongoose.Schema.Types.ObjectId, 
    ref: "Institution",
    default: null // null for general_public and donor types
  },
  classroomId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: "Classroom",
    default: null 
  },
  promoType: { 
    type: String, 
    enum: ['school', 'college', 'general_public', 'donor'],
    required: true 
  },
  classLevel: { 
    type: String,
    default: null 
    // KG, 1-10 for school OR PreMed, 
    // PreEng, Commerce, ALevels, OLevels for college
  },
  batchYear: {
    type: String,
    default: null 
  },
  isActive: { type: Boolean, default: true },
  usageCount: { type: Number, default: 0 }
}, { 
  timestamps: true,
  collection: "PromoCodes" 
});

module.exports = mongoose.model("PromoCode", promoCodeSchema);
