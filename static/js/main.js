// main.js — client-side JS for Spendly. No frameworks, vanilla only.

(function () {
  "use strict";

  const MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
  ];
  const WEEKDAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

  const pad = (n) => String(n).padStart(2, "0");
  const toISO = (y, m, d) => `${y}-${pad(m)}-${pad(d)}`;
  const fmtDisplay = (iso) => {
    if (!iso || !/^\d{4}-\d{2}-\d{2}$/.test(iso)) return "";
    const [y, m, d] = iso.split("-").map(Number);
    return `${d} ${MONTHS[m - 1].slice(0, 3)} ${y}`;
  };
  const daysInMonth = (y, m) => new Date(y, m, 0).getDate();

  function initialView(iso) {
    if (iso && /^\d{4}-\d{2}-\d{2}$/.test(iso)) {
      const [y, m] = iso.split("-").map(Number);
      return { y, m };
    }
    const t = new Date();
    return { y: t.getFullYear(), m: t.getMonth() + 1 };
  }

  function initPicker(picker) {
    const trigger = picker.querySelector(".profile-date-trigger");
    const display = picker.querySelector(".profile-filter-date-display");
    const hidden = picker.querySelector('input[type="hidden"]');
    const cal = picker.querySelector(".profile-calendar");
    const monthSelect = document.querySelector(".profile-filter-month select");

    let view = initialView(hidden.value);

    function render() {
      const firstDay = new Date(view.y, view.m - 1, 1).getDay();
      const total = daysInMonth(view.y, view.m);
      let html = '<div class="cal-header">';
      html += '<button type="button" class="cal-nav cal-prev" aria-label="Previous month">&lsaquo;</button>';
      html += `<span class="cal-title">${MONTHS[view.m - 1]} ${view.y}</span>`;
      html += '<button type="button" class="cal-nav cal-next" aria-label="Next month">&rsaquo;</button>';
      html += "</div>";
      html += '<div class="cal-weekdays">';
      WEEKDAYS.forEach((w) => (html += `<span>${w}</span>`));
      html += "</div>";
      html += '<div class="cal-grid">';
      for (let i = 0; i < firstDay; i++) html += '<span class="cal-cell cal-empty"></span>';
      for (let d = 1; d <= total; d++) {
        const iso = toISO(view.y, view.m, d);
        const cls = "cal-cell cal-day" + (iso === hidden.value ? " cal-selected" : "");
        html += `<button type="button" class="${cls}" data-iso="${iso}">${d}</button>`;
      }
      html += "</div>";
      cal.innerHTML = html;
    }

    function open() {
      document.querySelectorAll(".profile-calendar").forEach((c) => {
        if (c !== cal) c.hidden = true;
      });
      render();
      cal.hidden = false;
    }
    function close() {
      cal.hidden = true;
    }

    trigger.addEventListener("click", (e) => {
      e.stopPropagation();
      cal.hidden ? open() : close();
    });

    cal.addEventListener("click", (e) => {
      const nav = e.target.closest(".cal-nav");
      if (nav) {
        if (nav.classList.contains("cal-prev")) view.m--;
        else view.m++;
        if (view.m < 1) { view.m = 12; view.y--; }
        if (view.m > 12) { view.m = 1; view.y++; }
        render();
        return;
      }
      const day = e.target.closest(".cal-day");
      if (day) {
        const iso = day.dataset.iso;
        hidden.value = iso;
        display.value = fmtDisplay(iso);
        if (monthSelect) monthSelect.value = ""; // manual pick clears the month preset
        close();
      }
    });

    // Format any pre-selected value for display on load.
    display.value = fmtDisplay(hidden.value);
  }

  // Close any open calendar popover when clicking outside every date picker.
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".profile-date-picker")) {
      document.querySelectorAll(".profile-calendar").forEach((c) => (c.hidden = true));
    }
  });

  document.addEventListener("DOMContentLoaded", () => {
    // Choosing a month clears any manually-picked from/to so the URL stays clean.
    const monthSelect = document.querySelector(".profile-filter-month select");
    if (monthSelect) {
      monthSelect.addEventListener("change", () => {
        document
          .querySelectorAll(
            '.profile-date-picker input[type="hidden"][name="start"], ' +
            '.profile-date-picker input[type="hidden"][name="end"]'
          )
          .forEach((el) => (el.value = ""));
        monthSelect.form.submit();
      });
    }
    document.querySelectorAll(".profile-date-picker").forEach(initPicker);
  });
})();
