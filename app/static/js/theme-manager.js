// Theme Manager - Handle color palette switching & Premium UI
class ThemeManager {
    constructor() {
        this.storageKey = 'bpo-theme-preference';
        this.darkKey = 'bpo-dark-mode';
        this.darkThemeSuffix = '-dark';

        this.themes = [
            { id: 'default', name: 'Ocean', color: '#2563eb' },
            { id: 'forest', name: 'Forest', color: '#059669' },
            { id: 'amethyst', name: 'Amethyst', color: '#7c3aed' },
            { id: 'sunset', name: 'Sunset', color: '#f97316' }, // New
            { id: 'berry', name: 'Berry', color: '#ec4899' },   // New
            { id: 'citrus', name: 'Citrus', color: '#c5d912' }, // New (User Requested)
        ];

        this.init();
    }

    init() {
        // 1. Apply saved preferences immediately
        this.applyCurrentTheme();

        // 2. Setup the new UI (replace old selectors)
        // Wait for DOM if run before loaded, though usually this script is at end of body
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupUI());
        } else {
            this.setupUI();
        }
    }

    setupUI() {
        const container = document.getElementById('theme-container');
        if (!container) return; // Should exist in base layout

        // Clear existing inline content (swatches + toggle)
        container.innerHTML = '';

        // Inject Trigger Button
        const triggerBtn = document.createElement('button');
        triggerBtn.className = 'theme-trigger-btn';
        triggerBtn.title = 'Customize Appearance';
        triggerBtn.innerHTML = '<iconify-icon icon="solar:palette-bold-duotone" class="text-xl"></iconify-icon>';

        triggerBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.togglePanel();
        });

        container.appendChild(triggerBtn);

        // Inject Settings Panel into Body (to avoid z-index issues)
        this.injectSettingsPanel();

        // Close panel when clicking outside
        document.addEventListener('click', (e) => {
            const panel = document.getElementById('theme-settings-panel');
            if (panel &&
                panel.classList.contains('open') &&
                !panel.contains(e.target) &&
                !triggerBtn.contains(e.target)) {
                this.closePanel();
            }
        });
    }

    injectSettingsPanel() {
        // Remove existing if any (dev hot reload safety)
        const existing = document.getElementById('theme-settings-panel');
        if (existing) existing.remove();

        const panel = document.createElement('div');
        panel.id = 'theme-settings-panel';
        panel.className = 'theme-settings-panel';

        // Header
        const header = document.createElement('div');
        header.className = 'panel-header';
        header.innerHTML = `
            <span class="panel-title">Appearance</span>
            <button class="panel-close" id="close-theme-panel">
                <iconify-icon icon="solar:close-circle-bold" class="text-xl"></iconify-icon>
            </button>
        `;
        panel.appendChild(header);

        // Theme Grid Section
        const themeLabel = document.createElement('div');
        themeLabel.className = 'panel-section-label';
        themeLabel.textContent = 'Accent Color';
        panel.appendChild(themeLabel);

        const grid = document.createElement('div');
        grid.className = 'theme-grid';

        this.themes.forEach(theme => {
            const card = document.createElement('button');
            card.className = 'theme-card';
            card.dataset.theme = theme.id;
            card.innerHTML = `
                <div class="theme-preview" style="--theme-color: ${theme.color}"></div>
                <span class="theme-name">${theme.name}</span>
            `;
            card.addEventListener('click', () => this.setTheme(theme.id));
            grid.appendChild(card);
        });
        panel.appendChild(grid);

        // Dark Mode Section
        const modeLabel = document.createElement('div');
        modeLabel.className = 'panel-section-label';
        modeLabel.textContent = 'Interface Mode';
        panel.appendChild(modeLabel);

        const appearanceRow = document.createElement('div');
        appearanceRow.className = 'appearance-row';
        appearanceRow.innerHTML = `
            <div class="appearance-label">
                <iconify-icon icon="solar:moon-stars-bold-duotone" class="text-xl text-primary"></iconify-icon>
                <span>Dark Mode</span>
            </div>
            <input type="checkbox" class="toggle-switch" id="panel-dark-toggle">
        `;
        panel.appendChild(appearanceRow);

        // Append to DOM body
        document.body.appendChild(panel);

        // Bind events
        document.getElementById('close-theme-panel').addEventListener('click', () => this.closePanel());

        const darkToggle = document.getElementById('panel-dark-toggle');
        darkToggle.addEventListener('change', (e) => this.toggleDarkMode(e.target.checked));

        // Sync initial state
        this.updateActiveState();
    }

    togglePanel() {
        const panel = document.getElementById('theme-settings-panel');
        if (!panel) return;

        if (panel.classList.contains('open')) {
            this.closePanel();
        } else {
            this.openPanel();
        }
    }

    openPanel() {
        const panel = document.getElementById('theme-settings-panel');
        if (panel) {
            panel.classList.add('open');
            this.updateActiveState(); // Ensure UI sync before showing
        }
    }

    closePanel() {
        const panel = document.getElementById('theme-settings-panel');
        if (panel) panel.classList.remove('open');
    }

    toggleDarkMode(enable) {
        if (enable) {
            document.documentElement.classList.add('dark');
            localStorage.setItem(this.darkKey, 'true');
        } else {
            document.documentElement.classList.remove('dark');
            localStorage.setItem(this.darkKey, 'false');
        }
        this.applyCurrentTheme(); // Re-apply to switch between light/dark palette
    }

    applyCurrentTheme() {
        const isDarkMode = localStorage.getItem(this.darkKey) === 'true';
        let baseThemeId = localStorage.getItem(this.storageKey) || 'default';

        // Ensure valid theme
        if (!this.themes.find(t => t.id === baseThemeId)) {
            baseThemeId = 'default';
        }

        let effectiveThemeId = baseThemeId;
        if (isDarkMode) {
            effectiveThemeId += this.darkThemeSuffix;
        }

        document.documentElement.setAttribute('data-theme', effectiveThemeId);

        // Sync UI toggles if they exist
        const darkToggle = document.getElementById('panel-dark-toggle');
        if (darkToggle) {
            darkToggle.checked = isDarkMode;
        }

        // Sync old method just in case (optional, depending on other scripts)
        if (isDarkMode) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }

        this.updateActiveThemeUI(baseThemeId);
    }

    setTheme(baseThemeId) {
        localStorage.setItem(this.storageKey, baseThemeId);
        this.applyCurrentTheme();
    }

    updateActiveThemeUI(activeBaseThemeId) {
        const cards = document.querySelectorAll('.theme-card');
        cards.forEach(card => {
            if (card.dataset.theme === activeBaseThemeId) {
                card.classList.add('active');
            } else {
                card.classList.remove('active');
            }
        });
    }

    updateActiveState() {
        const isDarkMode = localStorage.getItem(this.darkKey) === 'true';
        const baseThemeId = localStorage.getItem(this.storageKey) || 'default';

        const darkToggle = document.getElementById('panel-dark-toggle');
        if (darkToggle) darkToggle.checked = isDarkMode;

        this.updateActiveThemeUI(baseThemeId);
    }
}

// Initialize theme manager
new ThemeManager();
