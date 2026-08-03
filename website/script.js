// ─── Hero Slider ─────────────────────────────
let currentSlide = 0;
const track = document.getElementById('heroTrack');
const dots = document.querySelectorAll('.hero-dot');
const slides = document.querySelectorAll('.hero-slide');
const totalSlides = slides.length;
let autoSlideInterval;
const isMobile = () => window.innerWidth <= 900;

function goToSlide(index) {
    if (index < 0) index = totalSlides - 1;
    if (index >= totalSlides) index = 0;
    currentSlide = index;

    if (isMobile()) {
        // Mobile : fade in/out par classe active
        slides.forEach((s, i) => {
            s.classList.toggle('active', i === currentSlide);
        });
    } else {
        // Desktop : translation horizontale
        track.style.transform = `translateX(-${currentSlide * 100}%)`;
    }

    dots.forEach((d, i) => d.classList.toggle('active', i === currentSlide));
}

function nextSlide() { goToSlide(currentSlide + 1); }
function prevSlide() { goToSlide(currentSlide - 1); }

function startAutoSlide() { stopAutoSlide(); autoSlideInterval = setInterval(nextSlide, 5500); }
function stopAutoSlide() { clearInterval(autoSlideInterval); }
function restartAutoSlide() { startAutoSlide(); }

// ─── Events ─────────────────────────────────
document.getElementById('heroNext').addEventListener('click', () => { nextSlide(); restartAutoSlide(); });
document.getElementById('heroPrev').addEventListener('click', () => { prevSlide(); restartAutoSlide(); });
dots.forEach(dot => {
    dot.addEventListener('click', () => { goToSlide(parseInt(dot.dataset.slide)); restartAutoSlide(); });
});

// Pause hover
const sliderEl = document.querySelector('.hero-slider');
sliderEl.addEventListener('mouseenter', stopAutoSlide);
sliderEl.addEventListener('mouseleave', startAutoSlide);

// Touch swipe (desktop)
let touchStartX = 0;
sliderEl.addEventListener('touchstart', e => { touchStartX = e.changedTouches[0].screenX; }, { passive: true });
sliderEl.addEventListener('touchend', e => {
    const diff = touchStartX - e.changedTouches[0].screenX;
    if (Math.abs(diff) > 50) {
        if (diff > 0) nextSlide(); else prevSlide();
        restartAutoSlide();
    }
}, { passive: true });

// ─── Re-init on resize (mobile ↔ desktop) ────
let lastIsMobile = isMobile();
window.addEventListener('resize', () => {
    const nowMobile = isMobile();
    if (nowMobile !== lastIsMobile) {
        lastIsMobile = nowMobile;
        // Reset : afficher le slide 0 dans le nouveau mode
        if (nowMobile) {
            track.style.transform = '';
            slides.forEach((s, i) => s.classList.toggle('active', i === 0));
        } else {
            slides.forEach(s => s.classList.remove('active'));
        }
        goToSlide(0);
    }
});

// ─── Démarrer ───────────────────────────────
// Initialiser l'état mobile au chargement
if (isMobile()) {
    slides.forEach((s, i) => s.classList.toggle('active', i === 0));
}
startAutoSlide();

// ─── Navigation mobile toggle ─────────────────
document.getElementById('navToggle').addEventListener('click', () => {
    document.getElementById('navLinks').classList.toggle('open');
});

// ─── Scroll + active link ─────────────────────
const nav = document.querySelector('.navbar');
const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('.nav-links a');

window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 10);
    let current = '';
    sections.forEach(section => {
        const top = section.offsetTop - 120;
        if (window.scrollY >= top) current = section.getAttribute('id');
    });
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === '#' + current) link.classList.add('active');
    });
});

// ─── Smooth scroll anchors ─────────────────────
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        document.getElementById('navLinks').classList.remove('open');
    });
});
