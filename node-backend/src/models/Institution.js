const mongoose = require("mongoose");

const institutionSchema = new mongoose.Schema({
  name: { type: String, required: true },
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true },
  
  // initials: { type: String, required: true, uppercase: true },
  address: { type: String },
}, { timestamps: true });

module.exports = mongoose.model("Institution", institutionSchema);
