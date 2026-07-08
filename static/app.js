// المدير المالي — تفاعلات بسيطة (بدون سكربتات مضمّنة، متوافق مع CSP)
(function () {
  "use strict";
  document.addEventListener("DOMContentLoaded", function () {
    var drop = document.getElementById("drop");
    var input = document.getElementById("file");
    var fname = document.getElementById("fname");
    var form = document.getElementById("form");
    var btn = document.getElementById("btn");

    function show(name) {
      if (fname) { fname.textContent = name; fname.style.display = "block"; }
    }

    if (drop && input) {
      drop.addEventListener("click", function () { input.click(); });
      drop.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); input.click(); }
      });
      input.addEventListener("change", function () {
        if (input.files.length) show(input.files[0].name);
      });
      ["dragover", "dragenter"].forEach(function (ev) {
        drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add("over"); });
      });
      ["dragleave", "drop"].forEach(function (ev) {
        drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.remove("over"); });
      });
      drop.addEventListener("drop", function (e) {
        if (e.dataTransfer && e.dataTransfer.files.length) {
          input.files = e.dataTransfer.files;
          show(e.dataTransfer.files[0].name);
        }
      });
    }

    if (form && btn) {
      form.addEventListener("submit", function () {
        if (input && !input.files.length) return;   // دع المتصفح يطالب بالملف
        btn.disabled = true;
        // رسائل متتابعة تطمئن المستخدم أن التحليل يعمل (كشف حقيقي قد يأخذ ~دقيقة)
        var steps = (btn.getAttribute("data-steps") || "…").split("|");
        var i = 0;
        btn.textContent = steps[0];
        setInterval(function () {
          i = (i + 1) % steps.length;
          btn.textContent = steps[i];
        }, 2200);
      });
    }
  });
})();
