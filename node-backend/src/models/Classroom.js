const mongoose = require("mongoose");

const classroomSchema = new mongoose.Schema({
  schoolId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: "Institution",
    required: true,
  },
  className: { type: String, required: true }, 
  section: { type: String, required: true },
  schoolInitials: { type: String, required: true },  
  classCode: { type: String, required: true, unique: true },
  
  students: [{ type: mongoose.Schema.Types.ObjectId, ref: "Student" }] 
}, { timestamps: true });

module.exports = mongoose.model("Classroom", classroomSchema);