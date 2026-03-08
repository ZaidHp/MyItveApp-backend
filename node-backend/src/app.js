const express = require("express");
const cors = require("cors");
const classroomRoutes = require("./routes/classroomRoutes");
const promoCodeRoutes = require("./routes/promoCodeRoutes");
const institutionRoutes = require("./routes/institutionRoutes");

const app = express();

app.use(cors());
app.use(express.json());

// Default Route
app.get("/", (req, res) => {
  res.send("Student Course App API Running");
});

app.use("/api/classrooms", classroomRoutes);
app.use("/api/promo-codes", promoCodeRoutes);
app.use("/api/institutions", institutionRoutes);

module.exports = app;
