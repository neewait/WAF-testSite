// ===== Переключение сайдбара =====
const sidebar = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebarToggle');

if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
        // Меняем иконку стрелки
        const icon = sidebarToggle.querySelector('span');
        icon.textContent = sidebar.classList.contains('collapsed') ? '▶' : '◀';
        localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
    });
    
    // Восстанавливаем состояние сайдбара
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

// Загружаем сохранённую тему
const savedTheme = localStorage.getItem('theme') || 'light';
setTheme(savedTheme);

if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        const current = html.getAttribute('data-theme');
        setTheme(current === 'light' ? 'dark' : 'light');
    });
}

// ===== Группы в сайдбаре =====
document.querySelectorAll('.nav-group-toggle').forEach(toggle => {
    toggle.addEventListener('click', () => {
        const group = toggle.dataset.group;
        const children = document.getElementById(`group-${group}`);
        if (children) {
            children.classList.toggle('expanded');
        }
    });
});

// ===== Активная вкладка =====
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', function() {
        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        this.classList.add('active');
    });
});