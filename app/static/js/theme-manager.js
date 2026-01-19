// Theme Manager - Handle color palette switching
class ThemeManager {
    constructor() {
        this.storageKey = 'bpo-theme-preference';
        this.darkThemeSuffix = '-dark';
        this.themes = [
            { id: 'default', name: 'Default', color: '#2563eb' },
            { id: 'forest', name: 'Forest', color: '#059669' },
            { id: 'amethyst', name: 'Amethyst', color: '#7c3aed' },
        ];
        
        this.init();
    }

    init() {
        this.setupDarkModeToggle();
        this.setupThemeSelector();
        this.applyCurrentTheme();
    }

    applyCurrentTheme() {
        const isDarkMode = localStorage.getItem('bpo-dark-mode') === 'true';
        let themeId = localStorage.getItem(this.storageKey) || 'default';
        
        if (isDarkMode) {
            themeId += this.darkThemeSuffix;
        }
        
        this.setTheme(themeId);
    }

    setTheme(themeId) {
        document.documentElement.setAttribute('data-theme', themeId);
        
        // Save base theme (without -dark suffix)
        const baseThemeId = themeId.replace(this.darkThemeSuffix, '');
        localStorage.setItem(this.storageKey, baseThemeId);

        this.updateActiveThemeUI();
    }

    setupThemeSelector() {
        const themeSelector = document.getElementById('theme-selector');
        if (!themeSelector) return;

        // Create theme swatches
        this.themes.forEach(theme => {
            const swatch = document.createElement('button');
            swatch.classList.add('theme-swatch');
            swatch.setAttribute('data-theme-id', theme.id);
            swatch.setAttribute('title', theme.name);
            swatch.style.backgroundColor = theme.color;
            swatch.addEventListener('click', () => {
                const isDarkMode = localStorage.getItem('bpo-dark-mode') === 'true';
                let newThemeId = theme.id;
                if (isDarkMode) {
                    newThemeId += this.darkThemeSuffix;
                }
                this.setTheme(newThemeId);
            });
            themeSelector.appendChild(swatch);
        });

        this.updateActiveThemeUI();
    }

    setupDarkModeToggle() {
        const darkModeToggle = document.getElementById('dark-mode-toggle');
        if (!darkModeToggle) return;

        darkModeToggle.addEventListener('click', () => {
            const isDarkMode = document.documentElement.classList.toggle('dark');
            localStorage.setItem('bpo-dark-mode', isDarkMode);
            this.applyCurrentTheme();
        });

        // Set initial state
        if (localStorage.getItem('bpo-dark-mode') === 'true') {
            document.documentElement.classList.add('dark');
        }
    }

    updateActiveThemeUI() {
        const currentBaseTheme = localStorage.getItem(this.storageKey) || 'default';
        const swatches = document.querySelectorAll('.theme-swatch');
        swatches.forEach(swatch => {
            if (swatch.getAttribute('data-theme-id') === currentBaseTheme) {
                swatch.classList.add('active');
            } else {
                swatch.classList.remove('active');
            }
        });
    }
}

// Initialize theme manager
document.addEventListener('DOMContentLoaded', () => {
    new ThemeManager();
});
