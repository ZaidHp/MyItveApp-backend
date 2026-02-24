const jwt = require("jsonwebtoken");
const Institution = require("../models/Institution");
const Student = require("../models/Student");

const protectInstitution = async (req, res, next) => {
  let token;
  if (req.headers.authorization && req.headers.authorization.startsWith("Bearer")) {
    try {
      token = req.headers.authorization.split(" ")[1];
      const decoded = jwt.verify(token, process.env.JWT_SECRET);

      // Extract ID using 'sub' (FastAPI standard) or fallback to 'id'
      const userId = decoded.sub || decoded.id;

      req.school = await Institution.findById(userId).select("-password");

      if (!req.school) {
        return res.status(403).json({ message: "Not authorized as an Institution" });
      }
      next();
    } catch (error) {
      res.status(401).json({ message: "Not authorized, token failed" });
    }
  }

  if (!token) {
    res.status(401).json({ message: "Not authorized, no token" });
  }
};

const protectUser = async (req, res, next) => {
  let token;
  if (req.headers.authorization && req.headers.authorization.startsWith("Bearer")) {
    try {
      token = req.headers.authorization.split(" ")[1];
      const decoded = jwt.verify(token, process.env.JWT_SECRET);

      // Extract ID using 'sub' (FastAPI standard) or fallback to 'id'
      const userId = decoded.sub || decoded.id;

      const student = await Student.findById(userId).select("-password");
      if (student) {
        req.student = student;
        req.userRole = "student";
        return next();
      }

      const school = await Institution.findById(userId).select("-password");
      if (school) {
        req.school = school;
        req.userRole = "institution";
        return next();
      }

      return res.status(403).json({ message: "User not found in any role" });

    } catch (error) {
      console.error(error);
      res.status(401).json({ message: "Not authorized, token failed" });
    }
  }

  if (!token) {
    res.status(401).json({ message: "Not authorized, no token" });
  }
};

module.exports = { protectInstitution, protectUser };