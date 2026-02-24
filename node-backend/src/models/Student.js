// const mongoose = require("mongoose");

// const studentSchema = new mongoose.Schema({
//   name: { type: String, required: true },
//   email: { type: String, required: true, unique: true },
//   password: { type: String, required: true },

//   studentCode: { type: String, required: true, unique: true },
  
//   enrolledClassrooms: [{ 
//     type: mongoose.Schema.Types.ObjectId, 
//     ref: "Classroom" 
//   }]
// }, { timestamps: true });

// module.exports = mongoose.model("Student", studentSchema);

const mongoose = require("mongoose");

const studentSchema = new mongoose.Schema({
  name: { type: String, required: true },
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true },
  username: { type: String, unique: true, sparse: true },
  phone: { type: String },
  
  
  // studentCode: { type: String, unique: true, sparse: true }, 
  
  enrolledClassrooms: [{ 
    type: mongoose.Schema.Types.ObjectId, 
    ref: "Classroom" 
  }]
}, { 
  timestamps: true,
  collection: "Students"
});

module.exports = mongoose.model("Student", studentSchema);