const express = require("express");
const cors = require("cors");
const classroomRoutes = require("./routes/classroomRoutes");

const app = express();

app.use(cors());
app.use(express.json());

// Default Route
app.get("/", (req, res) => {
  res.send("Student Course App API Running");
});

app.use("/api/classrooms", classroomRoutes);

module.exports = app;
