/* Vetal Sand Solutions — Main JS */
document.addEventListener('DOMContentLoaded', function () {

    /* ── Active nav link highlight ── */
    const currentPath = window.location.pathname;
    document.querySelectorAll('.navbar-nav .nav-link').forEach(function (link) {
        const href = link.getAttribute('href');
        if (!href) return;
        /* Exact match, or starts-with for non-home prefixes */
        if (href === currentPath || (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });

    /* ── Navbar scroll shadow ── */
    const navbar = document.querySelector('.premium-navbar');
    if (navbar) {
        const onScroll = function () {
            if (window.scrollY > 12) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        };
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    }

    /* ── Product filter: auto-submit on select change ── */
    const filterSelects = document.querySelectorAll('.product-filter-select');
    filterSelects.forEach(function (sel) {
        sel.addEventListener('change', function () {
            const form = sel.closest('form');
            if (form) form.submit();
        });
    });

    /* ── Payment method card visual feedback ── */
    document.querySelectorAll('.payment-method-card input[type="radio"]').forEach(function (radio) {
        radio.addEventListener('change', function () {
            document.querySelectorAll('.payment-method-card').forEach(function (card) {
                card.classList.remove('is-selected');
            });
            radio.closest('.payment-method-card').classList.add('is-selected');
        });
        if (radio.checked) {
            radio.closest('.payment-method-card').classList.add('is-selected');
        }
    });

    /* ── Close mobile offcanvas drawer on nav link click ── */
    const offcanvasEl = document.getElementById('mainNavbar');
    if (offcanvasEl && typeof bootstrap !== 'undefined' && bootstrap.Offcanvas) {
        offcanvasEl.querySelectorAll('.nav-link, .mobile-drawer-item').forEach(function (link) {
            link.addEventListener('click', function () {
                const offcanvasInstance = bootstrap.Offcanvas.getInstance(offcanvasEl);
                if (offcanvasInstance) {
                    offcanvasInstance.hide();
                }
            });
        });
    }

});

