(function () {
  const STYLE_ID = "reddit-dot-vector-style";
  const TARGET_CLASS = "reddit-dot-vector-target";

  const RAW_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="#FF4500" stroke-width="2"/><path d="M5 8l2 2 4-4" stroke="#FF4500" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  const ICON_DATA_URI = `url("data:image/svg+xml,${encodeURIComponent(RAW_SVG)}")`;

  function ensureStyleElement() {
    if (document.getElementById(STYLE_ID)) {
      return;
    }

    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = `
      .${TARGET_CLASS} {
        position: relative;
        padding-left: 22px;
      }

      .${TARGET_CLASS}::before {
        content: "";
        position: absolute;
        left: 0;
        top: 0.35rem;
        width: 16px;
        height: 16px;
        background-image: ${ICON_DATA_URI};
        background-size: 16px 16px;
        background-repeat: no-repeat;
      }
    `;
    document.head.appendChild(style);
  }

  function injectVectors(root = document) {
    ensureStyleElement();
    const targets = root.querySelectorAll('[id$="-post-rtjson-content"]');

    targets.forEach((target) => {
      if (target.classList.contains(TARGET_CLASS)) {
        return;
      }

      target.classList.add(TARGET_CLASS);
    });
  }

  window.RedditVectorHelpers = Object.assign({}, window.RedditVectorHelpers, {
    injectVectors,
  });
})();
