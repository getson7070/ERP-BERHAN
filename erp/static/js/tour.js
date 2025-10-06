(() => {
    const btn = document.getElementById('start-tour');
    if (!btn || localStorage.getItem('onboarding-tour-done')) return;
    const steps = [
        { el: '.navbar-brand', text: window.tourStrings?.nav || 'Use the navigation menu to switch modules.' },
        { el: '#lang-select', text: window.tourStrings?.language || 'Change the interface language.' },
        { el: '#themeToggle', text: window.tourStrings?.theme || 'Toggle dark mode to reduce eye strain.' }
    ];
    let index = 0;
    function showStep() {
        const step = steps[index];
        const element = document.querySelector(step.el);
        if (!element) return;
        const popover = new bootstrap.Popover(element, {
            content: step.text,
            trigger: 'manual',
            placement: 'bottom'
        });
        popover.show();
        element.addEventListener('click', next, { once: true });
        element.focus();
    }
    function next() {
        const prev = document.querySelector(steps[index].el);
        bootstrap.Popover.getInstance(prev)?.hide();
        index += 1;
        if (index < steps.length) {
            showStep();
        } else {
            localStorage.setItem('onboarding-tour-done', '1');
        }
    }
    btn.addEventListener('click', showStep);
})();
