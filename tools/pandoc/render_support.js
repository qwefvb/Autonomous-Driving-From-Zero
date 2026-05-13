(function () {
  function addRenderNotice(kind, message) {
    if (document.querySelector(`[data-render-notice="${kind}"]`)) {
      return;
    }

    var notice = document.createElement("div");
    notice.className = "render-notice render-notice-" + kind;
    notice.setAttribute("data-render-notice", kind);
    notice.textContent = message;

    var container = document.querySelector("main") || document.body;
    container.insertBefore(notice, container.firstChild);
  }

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var script = document.createElement("script");
      script.src = src;
      script.async = true;
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  async function initMermaid() {
    var mermaidBlocks = document.querySelectorAll(".mermaid");
    if (!mermaidBlocks.length) {
      return;
    }

    try {
      var module = await import("https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs");
      var mermaid = module.default;

      mermaid.initialize({
        startOnLoad: false,
        theme: "base",
        securityLevel: "loose",
        themeVariables: {
          fontFamily: "Avenir Next, Segoe UI, PingFang SC, Hiragino Sans GB, sans-serif",
          primaryColor: "#f6ede0",
          primaryTextColor: "#18222f",
          primaryBorderColor: "#c97339",
          lineColor: "#94572e",
          secondaryColor: "#f3f0e8",
          tertiaryColor: "#fffdf8"
        }
      });

      await mermaid.run({ querySelector: ".mermaid" });
      document.documentElement.dataset.mermaid = "loaded";
    } catch (error) {
      document.documentElement.dataset.mermaid = "failed";
      addRenderNotice(
        "mermaid",
        "Mermaid 图未渲染。当前 HTML 会在浏览器运行时从 CDN 加载 Mermaid；如果离线或网络受限，图会保持为源码块。"
      );
      console.warn("Mermaid failed to load.", error);
    }
  }

  async function initMathJax() {
    if (!document.body.textContent.includes("$")) {
      return;
    }

    window.MathJax = {
      tex: {
        inlineMath: [["$", "$"], ["\\(", "\\)"]],
        displayMath: [["$$", "$$"], ["\\[", "\\]"]]
      },
      options: {
        skipHtmlTags: ["script", "noscript", "style", "textarea", "pre", "code"]
      }
    };

    try {
      await loadScript("https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js");
      document.documentElement.dataset.mathjax = "loaded";
    } catch (error) {
      document.documentElement.dataset.mathjax = "failed";
      addRenderNotice(
        "mathjax",
        "数学公式未渲染。当前 HTML 会在浏览器运行时从 CDN 加载 MathJax；如果离线或网络受限，公式会保持为源码。"
      );
      console.warn("MathJax failed to load.", error);
    }
  }

  window.addEventListener("DOMContentLoaded", function () {
    initMermaid();
    initMathJax();
  });
})();
