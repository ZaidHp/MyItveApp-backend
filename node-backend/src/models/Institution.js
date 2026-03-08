// const mongoose = require("mongoose");

// const institutionSchema = new mongoose.Schema({
//   name: { type: String, required: true },
//   email: { type: String, required: true, unique: true },
//   password: { type: String, required: true },
  
//   // initials: { type: String, required: true, uppercase: true },
//   address: { type: String },
// }, { timestamps: true });

// module.exports = mongoose.model("Institution", institutionSchema);


const mongoose = require("mongoose");

const institutionSchema = new mongoose.Schema({
  institute_name: { type: String, required: true },
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true },
  phone: { type: String },
  address: { type: String },
  head_of_institute: { type: String },
  user_type: { 
    type: String, 
    enum: ['school', 'college'],
    required: true 
  },
  initials: { type: String }
}, { 
  timestamps: true,
  collection: "Schools"
});

module.exports = mongoose.model("Institution", institutionSchema);