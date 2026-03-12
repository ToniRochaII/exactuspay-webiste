document.addEventListener('DOMContentLoaded', function() {
    // Fade-in animation on scroll for sections
    const observerOptions = { threshold: 0.1 };
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = "1";
                entry.target.style.transform = "translateY(0)";
            }
        });
    }, observerOptions);

    document.querySelectorAll('section').forEach(section => {
        section.style.opacity = "0";
        section.style.transform = "translateY(20px)";
        section.style.transition = "all 0.8s ease-out";
        observer.observe(section);
    });

    // Animate floating cards
    const cards = document.querySelectorAll('.floating-card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.5}s`;
    });
    
    // Animated counter for stats
    const stats = document.querySelectorAll('.stat-number');
    const statObserverOptions = { threshold: 0.5, rootMargin: '0px' };
    
    const statObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const stat = entry.target;
                const target = parseFloat(stat.textContent.replace(/[^0-9.]/g, ''));
                const hasPercent = stat.textContent.includes('%');
                const hasPlus = stat.textContent.includes('+');
                let current = 0;
                const increment = target / 50;
                
                const updateStat = () => {
                    if (current < target) {
                        current += increment;
                        if (current >= target) {
                            stat.textContent = target.toFixed(target % 1 === 0 ? 0 : 1) + (hasPercent ? '%' : '') + (hasPlus ? '+' : '');
                        } else {
                            stat.textContent = Math.floor(current) + (hasPercent ? '%' : '') + (hasPlus ? '+' : '');
                            setTimeout(updateStat, 30);
                        }
                    }
                };
                updateStat();
                statObserver.unobserve(stat);
            }
        });
    }, statObserverOptions);
    
    stats.forEach(stat => statObserver.observe(stat));
    
    // Header scroll effect
    let lastScroll = 0;
    const header = document.querySelector('header');
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > lastScroll && currentScroll > 100) {
            header.style.transform = 'translateY(-100%)';
        } else {
            header.style.transform = 'translateY(0)';
        }
        
        if (currentScroll > 50) {
            header.style.boxShadow = '0 10px 30px rgba(0,0,0,0.3)';
            header.style.backdropFilter = 'blur(20px)';
        } else {
            header.style.boxShadow = 'var(--shadow-sm)';
            header.style.backdropFilter = 'blur(10px)';
        }
        
        lastScroll = currentScroll;
    });
});