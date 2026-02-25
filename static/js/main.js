// ===== Переключение сайдбара =====
const sidebar = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebarToggle');

if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
        const icon = sidebarToggle.querySelector('span');
        icon.textContent = sidebar.classList.contains('collapsed') ? '▶' : '◀';
        localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
    });
    
    if (localStorage.getItem('sidebarCollapsed') === 'true') {
        sidebar.classList.add('collapsed');
        sidebarToggle.querySelector('span').textContent = '▶';
    }
}

// ===== Переключение темы =====
const themeToggle = document.getElementById('themeToggle');
const html = document.documentElement;

function setTheme(theme) {
    html.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
}

const savedTheme = localStorage.getItem('theme') || 'light';
setTheme(savedTheme);

if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        const current = html.getAttribute('data-theme');
        setTheme(current === 'light' ? 'dark' : 'light');
    });
}

// ===== Группы в сайдбаре (раскрытие подменю) =====
document.querySelectorAll('.nav-group-toggle').forEach(toggle => {
    toggle.addEventListener('click', () => {
        const group = toggle.dataset.group;
        const children = document.getElementById(`group-${group}`);
        if (children) {
            children.classList.toggle('expanded');
        }
    });
});

// ===== Подсветка активной вкладки при загрузке страницы =====
document.addEventListener('DOMContentLoaded', () => {
    const currentPath = window.location.pathname;
    const currentHash = window.location.hash;
    
    document.querySelectorAll('.nav-item').forEach(item => {
        const href = item.getAttribute('href');
        if (href) {
            const linkPath = href.split('#')[0];
            if (linkPath === currentPath) {
                document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
                item.classList.add('active');
            }
        }
    });
    
    // Для hash-вкладок внутри dashboard
    if (currentHash) {
        const target = document.querySelector(currentHash);
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    }
});
