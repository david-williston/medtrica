(() => {
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
    const groups = new Map();
    const buttons = document.querySelectorAll(
        '.button, button, [role="button"], .top-link, .pagination a, .category-nav a, #menu li:last-child a'
    );

    // As in Terry's project, each group starts at five seconds and staggers by one.
    buttons.forEach((button) => {
        const group = button.closest('.actions, .category-nav, .pagination, .product-contact, .header-nav') || button.parentElement;
        const index = groups.get(group) || 0;
        button.style.setProperty('--shine-delay', `calc(var(--shine-start) + var(--shine-stagger) * ${index})`);
        groups.set(group, index + 1);
    });

    if (preference.matches || !('IntersectionObserver' in window)) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(({ target, isIntersecting }) => {
            if (!isIntersecting) return;
            target.classList.add('motion-visible');
            observer.unobserve(target);
        });
    }, { rootMargin: '0px 0px -5% 0px', threshold: 0 });

    const targets = document.querySelectorAll(
        '.section-heading, .product-card, .post-entry, .company-band, .oem-band, ' +
        '.product-gallery > a, .product-contact, .post-content > h2, ' +
        '.post-content > blockquote, .product-information, .medtrica-footer'
    );
    targets.forEach((target) => {
        // Leave initially visible content alone, including restored scroll positions.
        if (target.getBoundingClientRect().top <= window.innerHeight) return;
        target.classList.add('motion-pending');
        observer.observe(target);
    });

    // Reveal everything immediately if the preference changes or an anchor receives focus.
    const revealAll = () => {
        observer.disconnect();
        document.querySelectorAll('.motion-pending').forEach((target) => {
            target.classList.add('motion-visible');
        });
    };
    preference.addEventListener('change', ({ matches }) => {
        if (matches) revealAll();
    });
    document.addEventListener('focusin', ({ target }) => {
        target.closest('.motion-pending')?.classList.add('motion-visible');
    });
    // Back/forward cache and in-page links should never leave their destinations hidden.
    window.addEventListener('pageshow', ({ persisted }) => {
        if (persisted) revealAll();
    });
    window.addEventListener('hashchange', revealAll);
})();
