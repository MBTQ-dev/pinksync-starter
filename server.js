
const express = require('express');
const path = require('path');
const app = express();

const PORT = process.env.PORT || 8080;

// Serve static files from the current directory
app.use(express.static(__dirname));

// Handle SPA routing: redirect all requests to index.html
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`PinkSync Node operational on port ${PORT}`);
  console.log(`Environment: ${process.env.NODE_ENV || 'production'}`);
});
