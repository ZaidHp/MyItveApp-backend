const Classroom = require("../models/Classroom");
const Student = require("../models/Student");

const createClassroom = async (req, res) => {
  try {
    const { className, section } = req.body;
    const schoolId = req.school._id;
    const schoolName = req.school.name;
    
    let finalInitials = "";

    const previousClass = await Classroom.findOne({ schoolId }).select("schoolInitials");

    if (previousClass) {
      finalInitials = previousClass.schoolInitials;
    } else {
      let base = schoolName
        .split(" ")
        .map(w => w[0])
        .join("")
        .replace(/[^A-Z]/gi, "")
        .toUpperCase();

      if (base.length < 2) base = "SCH";

      let candidate = base;
      let suffixChar = 65;

      while (true) {
        const conflict = await Classroom.findOne({ schoolInitials: candidate });

        if (!conflict) {
          finalInitials = candidate;
          break;
        }

        candidate = `${base}${String.fromCharCode(suffixChar)}`;
        suffixChar++;
        
        if (suffixChar > 90) { 
           suffixChar = 65; 
           base += "X"; 
        }
      }
    }

    const cleanClass = className.replace(/\s+/g, ""); 
    const cleanSection = section.replace(/\s+/g, "");
    
    const generatedCode = `${finalInitials}${cleanClass}${cleanSection}`;

    const duplicateClass = await Classroom.findOne({ classCode: generatedCode });
    if (duplicateClass) {
      return res.status(400).json({ 
        message: `Classroom code ${generatedCode} already exists.` 
      });
    }

    const classroom = await Classroom.create({
      schoolId: req.school._id,
      className,
      section,
      schoolInitials: finalInitials,
      classCode: generatedCode,
    });

    res.status(201).json({
      success: true,
      message: "Classroom created successfully",
      initialsUsed: finalInitials,
      data: classroom,
    });

  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Server Error", error: error.message });
  }
};

const validateClassCode = async (req, res) => {
  try {
    const { classCode } = req.params;

    const classroom = await Classroom.findOne({ classCode: classCode })
      .populate("schoolId", "name email address initials");

    if (!classroom) {
      return res.status(404).json({ 
        success: false, 
        message: "Invalid Classroom Code. Please check and try again." 
      });
    }

    res.status(200).json({
      success: true,
      data: {
        _id: classroom._id,
        classCode: classroom.classCode,
        className: classroom.className,
        section: classroom.section,
        school: {
          name: classroom.schoolId.name,
          email: classroom.schoolId.email,
          initials: classroom.schoolId.initials
        }
      }
    });

  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Server Error", error: error.message });
  }
};

const assignStudentToClass = async (req, res) => {
  try {
    const { classCode, studentCode } = req.body;

    if (!classCode) {
      return res.status(400).json({ message: "Please provide a Class Code." });
    }

    let studentToEnroll = null;

    if (req.userRole === "student") {
      studentToEnroll = req.student; 
      
    } else if (req.userRole === "institution") {
      if (!studentCode) {
        return res.status(400).json({ 
          message: "Schools must provide a 'studentCode' to assign a student." 
        });
      }

      studentToEnroll = await Student.findOne({ studentCode });
      if (!studentToEnroll) {
        return res.status(404).json({ message: `Student with code ${studentCode} not found.` });
      }

    } else {
      return res.status(401).json({ message: "Unauthorized." });
    }

    const classroom = await Classroom.findOne({ classCode });
    if (!classroom) {
      return res.status(404).json({ message: "Invalid Classroom Code." });
    }

    if (req.userRole === "institution") {
      if (classroom.schoolId.toString() !== req.school._id.toString()) {
        return res.status(403).json({ 
          message: "Unauthorized: You cannot enroll students in classes belonging to other schools." 
        });
      }
    }

    if (!classroom.students) classroom.students = [];
    if (!studentToEnroll.enrolledClassrooms) studentToEnroll.enrolledClassrooms = [];

    if (classroom.students.includes(studentToEnroll._id)) {
      return res.status(400).json({ 
        message: `Student '${studentToEnroll.name}' is already enrolled in this classroom.` 
      });
    }

    classroom.students.push(studentToEnroll._id);
    await classroom.save();

    studentToEnroll.enrolledClassrooms.push(classroom._id);
    await studentToEnroll.save();

    res.status(200).json({
      success: true,
      message: "Student assigned successfully.",
      data: {
        studentName: studentToEnroll.name,
        studentCode: studentToEnroll.studentCode,
        className: classroom.className,
        classCode: classroom.classCode
      }
    });

  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Server Error", error: error.message });
  }
};

const getClassStudentCount = async (req, res) => {
  try {
    const { classCode } = req.params;

    const classroom = await Classroom.findOne({ classCode });

    if (!classroom) {
      return res.status(404).json({ message: "Invalid Classroom Code." });
    }

    if (classroom.schoolId.toString() !== req.school._id.toString()) {
      return res.status(403).json({ 
        message: "Unauthorized: You can only view counts for your own classrooms." 
      });
    }

    const count = classroom.students ? classroom.students.length : 0;

    res.status(200).json({
      success: true,
      data: {
        classCode: classroom.classCode,
        className: classroom.className,
        section: classroom.section,
        totalStudents: count
      }
    });

  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Server Error", error: error.message });
  }
};

const getSchoolStudentCount = async (req, res) => {
  try {
    const schoolId = req.school._id;

    const classrooms = await Classroom.find({ schoolId }).select("students");

    const uniqueStudentIds = new Set();

    classrooms.forEach((classroom) => {
      if (classroom.students && classroom.students.length > 0) {
        classroom.students.forEach((studentId) => {
          uniqueStudentIds.add(studentId.toString());
        });
      }
    });

    res.status(200).json({
      success: true,
      data: {
        schoolName: req.school.name,
        initials: req.school.initials,
        totalClassrooms: classrooms.length,
        totalStudents: uniqueStudentIds.size
      }
    });

  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Server Error", error: error.message });
  }
};

module.exports = { createClassroom, validateClassCode, assignStudentToClass, getClassStudentCount, getSchoolStudentCount };