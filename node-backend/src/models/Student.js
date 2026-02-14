const mongoose = require("mongoose");

const studentSchema = new mongoose.Schema({
  name: { type: String, required: true },
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true },

  studentCode: { type: String, required: true, unique: true },
  
  enrolledClassrooms: [{ 
    type: mongoose.Schema.Types.ObjectId, 
    ref: "Classroom" 
  }]
}, { timestamps: true });

module.exports = mongoose.model("Student", studentSchema);