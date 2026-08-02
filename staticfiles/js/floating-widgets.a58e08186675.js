// HOODRANKED floating widgets: music player + currency converter.
// Track list is a plain array so this stays easy to edit without touching
// the markup — point src at real files in your static/audio/ folder.
const HOODRANKED_TRACKS = window.HOODRANKED_TRACKS || [];

document.addEventListener("DOMContentLoaded", () => {
  function initWidgetToggle(pillId, widgetId, bodyId, otherWidgetId, otherBodyId) {
    const pill = document.getElementById(pillId);
    const widget = document.getElementById(widgetId);
    const body = document.getElementById(bodyId);
    const otherWidget = document.getElementById(otherWidgetId);
    const otherBody = document.getElementById(otherBodyId);
    if (!pill || !widget || !body) return;

    pill.addEventListener("click", () => {
      const opening = !widget.classList.contains("expanded");

      if (opening && otherWidget?.classList.contains("expanded")) {
        otherWidget.classList.remove("expanded");
        otherBody.style.maxHeight = "0";
      }

      widget.classList.toggle("expanded", opening);
      if (opening) {
        requestAnimationFrame(() => {
          body.style.maxHeight = body.querySelector(".hr-widget-body-inner").scrollHeight + 32 + "px";
        });
      } else {
        body.style.maxHeight = "0";
      }
    });
  }

  initWidgetToggle("musicPill", "musicWidget", "musicBody", "currencyWidget", "currencyBody");
  initWidgetToggle("currencyPill", "currencyWidget", "currencyBody", "musicWidget", "musicBody");

  // --- Music player ---
  const audioEl = document.getElementById("audioEl");
  const vinyl = document.getElementById("vinyl");
  const playBtn = document.getElementById("playBtn");
  const playIcon = document.getElementById("playIcon");
  const trackNameEl = document.getElementById("trackName");
  const artistNameEl = document.getElementById("artistName");
  const progressFill = document.getElementById("progressFill");
  const currentTimeEl = document.getElementById("currentTime");
  const totalTimeEl = document.getElementById("totalTime");
  const pillTrackName = document.getElementById("pillTrackName");
  const musicPillEl = document.getElementById("musicPill");
  const volSlider = document.getElementById("volumeSlider");

  if (audioEl) {
    let currentTrack = 0;
    let isPlaying = false;
    let repeat = false;
    let shuffle = false;

    const fmt = (s) => `${Math.floor(s / 60)}:${(s % 60 | 0).toString().padStart(2, "0")}`;

    function loadTrack(idx, autoPlay = false) {
      const t = HOODRANKED_TRACKS[idx];
      trackNameEl.textContent = t.title;
      artistNameEl.textContent = t.artist;
      pillTrackName.textContent = t.title;
      progressFill.style.width = "0%";
      currentTimeEl.textContent = "0:00";

      if (t.src) {
        const cleanSrc = t.src.replaceAll('&amp;', '&');
        audioEl.src = cleanSrc;
        audioEl.load();
      }
      if (autoPlay && t.src) audioEl.play().then(() => setPlaying(true)).catch(() => {});
    }

    function setPlaying(state) {
      isPlaying = state;
      vinyl.classList.toggle("spinning", state);
      playIcon.innerHTML = state
        ? '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>'
        : '<path d="M8 5v14l11-7z"/>';
      musicPillEl.classList.toggle("is-playing", state);
    }

    audioEl.addEventListener("loadedmetadata", () => {
      totalTimeEl.textContent = fmt(Math.floor(audioEl.duration));
    });
    audioEl.addEventListener("timeupdate", () => {
      if (!audioEl.duration) return;
      progressFill.style.width = (audioEl.currentTime / audioEl.duration) * 100 + "%";
      currentTimeEl.textContent = fmt(Math.floor(audioEl.currentTime));
    });
    audioEl.addEventListener("ended", () => {
      if (repeat) {
        audioEl.currentTime = 0;
        audioEl.play();
      } else {
        skipNext();
      }
    });
    audioEl.addEventListener("play", () => setPlaying(true));
    audioEl.addEventListener("pause", () => setPlaying(false));

    volSlider?.addEventListener("input", () => {
      audioEl.volume = volSlider.value / 100;
    });
    audioEl.volume = 0.7;

    playBtn?.addEventListener("click", () => {
      if (!HOODRANKED_TRACKS[currentTrack].src) {
        setPlaying(!isPlaying);
        return;
      }
      isPlaying ? audioEl.pause() : audioEl.play().catch(() => {});
    });

    function skipNext() {
      currentTrack = shuffle
        ? Math.floor(Math.random() * HOODRANKED_TRACKS.length)
        : (currentTrack + 1) % HOODRANKED_TRACKS.length;
      loadTrack(currentTrack, true);
    }
    function skipPrev() {
      if (audioEl.src && audioEl.currentTime > 3) {
        audioEl.currentTime = 0;
        return;
      }
      currentTrack = (currentTrack - 1 + HOODRANKED_TRACKS.length) % HOODRANKED_TRACKS.length;
      loadTrack(currentTrack, true);
    }

    document.getElementById("nextBtn")?.addEventListener("click", skipNext);
    document.getElementById("prevBtn")?.addEventListener("click", skipPrev);
    document.getElementById("shuffleBtn")?.addEventListener("click", function () {
      shuffle = !shuffle;
      this.classList.toggle("p-active", shuffle);
    });
    document.getElementById("repeatBtn")?.addEventListener("click", function () {
      repeat = !repeat;
      audioEl.loop = repeat;
      this.classList.toggle("p-active", repeat);
    });
    document.getElementById("progressWrap")?.addEventListener("click", function (e) {
      const pct = (e.clientX - this.getBoundingClientRect().left) / this.offsetWidth;
      if (audioEl.duration) audioEl.currentTime = pct * audioEl.duration;
      progressFill.style.width = pct * 100 + "%";
    });

    loadTrack(0);
    // Autoplay requires a user gesture in most browsers — start on first interaction.
    document.addEventListener(
      "click",
      function startOnInteraction() {
        if (!isPlaying) audioEl.play().then(() => setPlaying(true)).catch(() => {});
        document.removeEventListener("click", startOnInteraction);
      },
      { once: true }
    );
  }

  // --- Currency converter ---
  const curTabs = document.getElementById("curTabs");
  if (curTabs) {
    let exchangeRates = {};
    let activeCur = "NGN";

    const getAllPrices = () =>
      Array.from(document.querySelectorAll("[data-ngn-price]"))
        .map((el) => parseFloat(el.dataset.ngnPrice))
        .filter((p) => !isNaN(p));
    const getDisplayPrice = () => {
      const p = getAllPrices();
      return p.length ? Math.min(...p) : null;
    };

    function updateSampleDisplay() {
      const price = getDisplayPrice();
      const sampleEl = document.getElementById("sampleNgn");
      sampleEl.textContent = price !== null ? price.toLocaleString("en-NG") : "—";
      if (price !== null) convertAndShow(price);
    }

    function convertAndShow(ngnAmount) {
      const convertedEl = document.getElementById("convertedVal");
      const rateEl = document.getElementById("rateInfo");
      if (activeCur === "NGN") {
        convertedEl.textContent = "₦" + ngnAmount.toLocaleString("en-NG");
        rateEl.textContent = "Nigerian Naira — base currency";
        return;
      }
      if (!exchangeRates[activeCur]) {
        convertedEl.innerHTML = '<span class="shimmer"></span>';
        return;
      }
      const tab = document.querySelector(`.cur-tab[data-code="${activeCur}"]`);
      const symbol = tab.dataset.symbol;
      const rate = exchangeRates[activeCur];
      convertedEl.textContent =
        symbol + (ngnAmount * rate).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      rateEl.textContent = `1 ${activeCur} ≈ ₦${(1 / rate).toLocaleString("en-NG", { maximumFractionDigits: 0 })}`;
    }

    function convertAllProductPrices() {
      document.querySelectorAll("[data-ngn-price]").forEach((el) => {
        const ngn = parseFloat(el.dataset.ngnPrice);
        if (isNaN(ngn)) return;
        if (activeCur === "NGN") {
          el.textContent = "₦" + ngn.toLocaleString("en-NG");
          return;
        }
        if (!exchangeRates[activeCur]) return;
        const tab = document.querySelector(`.cur-tab[data-code="${activeCur}"]`);
        el.textContent =
          tab.dataset.symbol +
          (ngn * exchangeRates[activeCur]).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      });
      document.getElementById("pillCurLabel").textContent = activeCur === "NGN" ? "CURRENCY" : activeCur;
    }

    async function fetchRates() {
      const dots = [document.getElementById("statusDot"), document.getElementById("statusDot2")];
      const txt = document.getElementById("statusText");
      try {
        const data = await (await fetch("https://open.er-api.com/v6/latest/NGN")).json();
        if (data.result === "success") {
          exchangeRates = data.rates;
          dots.forEach((d) => d.classList.add("live"));
          txt.textContent = "Live rates";
        } else {
          throw new Error("rate fetch failed");
        }
      } catch {
        exchangeRates = { NGN: 1, USD: 0.00063, GBP: 0.0005, CAD: 0.00086, EUR: 0.00058 };
        dots.forEach((d) => (d.style.background = "#f59e0b"));
        txt.textContent = "Cached rates";
      }
      updateSampleDisplay();
      convertAllProductPrices();
    }

    curTabs.addEventListener("click", (e) => {
      const tab = e.target.closest(".cur-tab");
      if (!tab) return;
      document.querySelectorAll(".cur-tab").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      activeCur = tab.dataset.code;
      document.getElementById("convertedVal").innerHTML = '<span class="shimmer"></span>';
      setTimeout(() => {
        updateSampleDisplay();
        convertAllProductPrices();
      }, 200);
    });

    fetchRates();
  }
});