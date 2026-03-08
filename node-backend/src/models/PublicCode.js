const mongoose = require("mongoose");

const publicCodeSchema = new mongoose.Schema({
  code: { type: String, required: true, unique: true },
  codeType: { 
    type: String, 
    enum: ['general_public', 'donor'],
    required: true 
  },
  donorType: {
    type: String,
    enum: ['Gold', 'Silver', 'Bronze', 'Platinum'],
    default: null 
  },
  batchYear: {
    type: String,
    default: null
  },
  isActive: { type: Boolean, default: true },
  usageCount: { type: Number, default: 0 }
}, { 
  timestamps: true,
  collection: "publiccodes" 
});

module.exports = mongoose.model("PublicCode", publicCodeSchema);
