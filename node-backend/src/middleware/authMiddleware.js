const jwt = require("jsonwebtoken");
const Institution = require("../models/Institution");
const Student = require("../models/Student");

const protectInstitution = async (req, res, next) => {
  let token;

  if (
    req.headers.authorization &&
    req.headers.authorization.startsWith("Bearer")
  ) {
    try {
      token = req.headers.authorization.split(" ")[1];

      const decoded = jwt.verify(token, process.env.JWT_SECRET);

      req.school = await Institution.findById(decoded.id).select("-password");

      if (!req.school) {
        return res.status(403).json({ message: "Not authorized as an Institution" });
      }

      next();
    } catch (error) {
      console.error(error);
      res.status(401).json({ message: "Not authorized, token failed" });
    }
  }

  if (!token) {
    res.status(401).json({ message: "Not authorized, no token" });
  }
};

const protectUser = async (req, res, next) => {
  let token;

  if (
    req.headers.authorization &&
    req.headers.authorization.startsWith("Bearer")
  ) {
    try {
      token = req.headers.authorization.split(" ")[1];
      const decoded = jwt.verify(token, process.env.JWT_SECRET);

      const student = await Student.findById(decoded.id).select("-password");
      if (student) {
        req.student = student;
        req.userRole = "student";
        return next();
      }

      const school = await Institution.findById(decoded.id).select("-password");
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