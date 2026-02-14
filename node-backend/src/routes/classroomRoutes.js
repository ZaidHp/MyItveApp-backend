const express = require("express");
const router = express.Router();
const { createClassroom, validateClassCode, assignStudentToClass, getClassStudentCount, getSchoolStudentCount } = require("../controllers/classroomController");
const { protectInstitution, protectUser } = require("../middleware/authMiddleware");

router.post("/create", protectInstitution, createClassroom);
router.get("/validate/:classCode", validateClassCode);
router.post("/assign", protectUser, assignStudentToClass);
router.get("/count/:classCode", protectInstitution, getClassStudentCount);
router.get("/school/total-students", protectInstitution, getSchoolStudentCount);

module.exports = router;