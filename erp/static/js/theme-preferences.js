(function () {
  const root = document.documentElement;
  const themeToggle = document.querySelector('[data-theme-toggle]');
  const contrastToggle = document.querySelector('[data-contrast-toggle]');
  const dynamicThemeMeta = document.querySelector('meta[data-dynamic-theme]');
  const themeStatus = document.querySelector('[data-theme-status]');
  const contrastStatus = document.querySelector('[data-contrast-status]');
  const STORAGE_KEYS = {
    theme: 'erp-ui-theme',
    contrast: 'erp-ui-contrast'
  };

  const safeStorage = (() => {
    try {
      const testKey = '__erp-ui__';
      window.localStorage.setItem(testKey, testKey);
      window.localStorage.removeItem(testKey);
      return window.localStorage;
    } catch (error) {
      return null;
    }
  })();

  const getStored = (key) => (safeStorage ? safeStorage.getItem(key) : null);
  const setStored = (key, value) => {
    if (!safeStorage) return;
    safeStorage.setItem(key, value);
  };

  const prefersDark = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
  const prefersHighContrast = window.matchMedia ? window.matchMedia('(prefers-contrast: more)') : null;
  const forcedColors = window.matchMedia ? window.matchMedia('(forced-colors: active)') : null;

  const resolveSystemTheme = () => (prefersDark && prefersDark.matches ? 'dark' : 'light');
  const resolveSystemContrast = () => (prefersHighContrast && prefersHighContrast.matches ? 'high' : 'normal');

  const setToggleDisabled = (toggle, disabled) => {
    if (!toggle) return;
    if (disabled) {
      toggle.setAttribute('aria-disabled', 'true');
      toggle.setAttribute('tabindex', '-1');
      if (typeof toggle.disabled !== 'undefined') {
        toggle.disabled = true;
      }
    } else {
      toggle.removeAttribute('aria-disabled');
      toggle.removeAttribute('tabindex');
      if (typeof toggle.disabled !== 'undefined') {
        toggle.disabled = false;
      }
    }
  };

  const setThemeColor = (theme) => {
    if (!dynamicThemeMeta) return;
    dynamicThemeMeta.setAttribute('content', theme === 'dark' ? '#0b1120' : '#f4f7fb');
  };

  function updateThemeToggle(theme) {
    if (!themeToggle) return;
    const isDark = theme === 'dark';
    const label = isDark ? themeToggle.dataset.darkLabel : themeToggle.dataset.lightLabel;
    const text = isDark ? themeToggle.dataset.darkText : themeToggle.dataset.lightText;
    const status = isDark ? themeToggle.dataset.darkStatus : themeToggle.dataset.lightStatus;
    themeToggle.setAttribute('aria-pressed', String(isDark));
    if (label) {
      themeToggle.setAttribute('aria-label', label);
    }
    if (text) {
      const textNode = themeToggle.querySelector('.toolbar-btn__text');
      if (textNode) {
        textNode.textContent = text;
      }
    }
    if (status && themeStatus) {
      themeStatus.textContent = status;
    }
  }

  function updateContrastToggle(mode) {
    if (!contrastToggle) return;
    const isHigh = mode === 'high';
    const label = isHigh ? contrastToggle.dataset.onLabel : contrastToggle.dataset.offLabel;
    const text = isHigh ? contrastToggle.dataset.onText : contrastToggle.dataset.offText;
    const status = isHigh ? contrastToggle.dataset.onStatus : contrastToggle.dataset.offStatus;
    contrastToggle.setAttribute('aria-pressed', String(isHigh));
    if (label) {
      contrastToggle.setAttribute('aria-label', label);
    }
    if (text) {
      const textNode = contrastToggle.querySelector('.toolbar-btn__text');
      if (textNode) {
        textNode.textContent = text;
      }
    }
    if (status && contrastStatus) {
      contrastStatus.textContent = status;
    }
  }

  function applyTheme(theme, persist = false) {
    const normalized = theme === 'light' ? 'light' : 'dark';
    root.setAttribute('data-theme', normalized);
    setThemeColor(normalized);
    if (persist) {
      setStored(STORAGE_KEYS.theme, normalized);
    }
    updateThemeToggle(normalized);
  }

  function applyContrast(mode, persist = false) {
    if (forcedColors && forcedColors.matches) {
      root.setAttribute('data-contrast', 'high');
      setToggleDisabled(contrastToggle, true);
      updateContrastToggle('high');
      return;
    }
    const normalized = mode === 'high' ? 'high' : 'normal';
    root.setAttribute('data-contrast', normalized);
    if (persist) {
      setStored(STORAGE_KEYS.contrast, normalized);
    }
    updateContrastToggle(normalized);
  }

  const storedTheme = getStored(STORAGE_KEYS.theme);
  if (storedTheme) {
    applyTheme(storedTheme);
  } else if (prefersDark && prefersDark.matches) {
    applyTheme('dark');
  } else {
    applyTheme('light');
  }

  const storedContrast = getStored(STORAGE_KEYS.contrast);
  if (forcedColors && forcedColors.matches) {
    applyContrast('high');
  } else if (storedContrast) {
    applyContrast(storedContrast);
  } else if (prefersHighContrast && prefersHighContrast.matches) {
    applyContrast('high');
  } else {
    applyContrast('normal');
  }

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const current = root.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      applyTheme(next, true);
    });
  }

  if (contrastToggle && !(forcedColors && forcedColors.matches)) {
    contrastToggle.addEventListener('click', () => {
      const current = root.getAttribute('data-contrast');
      const next = current === 'high' ? 'normal' : 'high';
      applyContrast(next, true);
    });
  }

  if (!storedTheme && prefersDark) {
    const handleThemeChange = (event) => {
      applyTheme(event.matches ? 'dark' : 'light');
    };
    if (typeof prefersDark.addEventListener === 'function') {
      prefersDark.addEventListener('change', handleThemeChange);
    } else if (typeof prefersDark.addListener === 'function') {
      prefersDark.addListener(handleThemeChange);
    }
  }

  if (!storedContrast && prefersHighContrast) {
    const handleContrastChange = (event) => {
      applyContrast(event.matches ? 'high' : 'normal');
    };
    if (typeof prefersHighContrast.addEventListener === 'function') {
      prefersHighContrast.addEventListener('change', handleContrastChange);
    } else if (typeof prefersHighContrast.addListener === 'function') {
      prefersHighContrast.addListener(handleContrastChange);
    }
  }

  if (forcedColors) {
    const handleForcedColors = (event) => {
      if (event.matches) {
        applyContrast('high');
      } else {
        setToggleDisabled(contrastToggle, false);
        const stored = getStored(STORAGE_KEYS.contrast) || 'normal';
        applyContrast(stored);
      }
    };
    if (typeof forcedColors.addEventListener === 'function') {
      forcedColors.addEventListener('change', handleForcedColors);
    } else if (typeof forcedColors.addListener === 'function') {
      forcedColors.addListener(handleForcedColors);
    }
  }

  if (window.addEventListener && safeStorage) {
    window.addEventListener('storage', (event) => {
      if (event.storageArea !== safeStorage) {
        return;
      }
      if (!event.key) {
        applyTheme(resolveSystemTheme());
        if (!(forcedColors && forcedColors.matches)) {
          applyContrast(resolveSystemContrast());
        }
        return;
      }

      if (event.key === STORAGE_KEYS.theme) {
        const nextTheme = event.newValue || resolveSystemTheme();
        applyTheme(nextTheme);
      }

      if (event.key === STORAGE_KEYS.contrast && !(forcedColors && forcedColors.matches)) {
        const nextContrast = event.newValue || resolveSystemContrast();
        applyContrast(nextContrast);
      }
    });
  }
})();
