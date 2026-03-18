/* PF Animations — count-up counters + highlight pulse
   Runs inside each slide iframe on DOMContentLoaded.
   Activated when theme.animations: true in presentation.yaml. */

(function () {
  'use strict';

  // Parse a display string like "€135M", "28", "4.2B", "92%" into components.
  // Regex: prefix (non-digit chars), numeric value, suffix (remaining chars)
  var RE = /^([^0-9]*)(\d+\.?\d*)(.*)$/;

  function parseValue(text) {
    var m = (text || '').trim().match(RE);
    if (!m) return null;
    var num = parseFloat(m[2]);
    if (isNaN(num)) return null;
    var decimals = m[2].indexOf('.') !== -1 ? (m[2].length - m[2].indexOf('.') - 1) : 0;
    return { prefix: m[1], target: num, suffix: m[3], decimals: decimals };
  }

  function easeOut(t) {
    return 1 - Math.pow(1 - t, 3);
  }

  function countUp(el) {
    var parsed = parseValue(el.textContent);
    if (!parsed) return;
    var start = performance.now();
    var duration = 900;
    var factor = Math.pow(10, parsed.decimals);

    function frame(now) {
      var elapsed = now - start;
      var t = Math.min(elapsed / duration, 1);
      var value = parsed.target * easeOut(t);
      var display = (Math.round(value * factor) / factor).toFixed(parsed.decimals);
      el.textContent = parsed.prefix + display + parsed.suffix;
      if (t < 1) requestAnimationFrame(frame);
    }

    requestAnimationFrame(frame);
  }

  document.addEventListener('DOMContentLoaded', function () {
    // Count-up on all stat values
    document.querySelectorAll('[data-count-up]').forEach(countUp);

    // Highlight pulse on flagged data points
    document.querySelectorAll('[data-highlight="primary"]').forEach(function (el) {
      el.classList.remove('pf-pulse-active');
      void el.offsetWidth; // force reflow to restart animation
      el.classList.add('pf-pulse-active');
    });
  });
})();
