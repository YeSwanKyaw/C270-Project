/**
 * Prefer: npm start  (from project root → ../app.js)
 * Kept so `cd web && npm start` still works.
 */
if (require.main === module) {
  require("../app.js").start();
} else {
  module.exports = require("../app.js");
}
