// Landing Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            navLinks.classList.toggle('active');
        });
    }
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Navbar background on scroll
    const navbar = document.querySelector('.navbar');
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.style.background = 'rgba(255, 255, 255, 0.98)';
            navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.1)';
        } else {
            navbar.style.background = 'rgba(255, 255, 255, 0.95)';
            navbar.style.boxShadow = 'none';
        }
    });
    
    // Animated counters for stats
    function animateCounter(element, target, duration = 2000) {
        let start = 0;
        const increment = target / (duration / 16);
        
        function updateCounter() {
            start += increment;
            if (start < target) {
                element.textContent = Math.floor(start).toLocaleString();
                requestAnimationFrame(updateCounter);
            } else {
                element.textContent = target.toLocaleString();
            }
        }
        
        updateCounter();
    }
    
    // Intersection Observer for animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                
                // Animate stats when they come into view
                if (entry.target.classList.contains('hero-stats')) {
                    const deploymentCount = document.getElementById('deployments-count');
                    const serverCount = document.getElementById('servers-count');
                    
                    if (deploymentCount && !deploymentCount.dataset.animated) {
                        animateCounter(deploymentCount, 1250);
                        deploymentCount.dataset.animated = 'true';
                    }
                    
                    if (serverCount && !serverCount.dataset.animated) {
                        animateCounter(serverCount, 15);
                        serverCount.dataset.animated = 'true';
                    }
                }
                
                // Animate metric bars when they come into view
                if (entry.target.classList.contains('metrics-card')) {
                    const metricFills = entry.target.querySelectorAll('.metric-fill');
                    metricFills.forEach((fill, index) => {
                        setTimeout(() => {
                            fill.style.transition = 'width 1s ease';
                            const width = fill.style.width;
                            fill.style.width = '0%';
                            setTimeout(() => {
                                fill.style.width = width;
                            }, 100);
                        }, index * 200);
                    });
                }
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    document.querySelectorAll('.feature-card, .step, .hero-stats, .metrics-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
    
    // Dashboard preview interactions
    const dashboardPreview = document.querySelector('.dashboard-preview');
    if (dashboardPreview) {
        dashboardPreview.addEventListener('mouseenter', function() {
            this.style.transform = 'perspective(1000px) rotateY(-5deg) rotateX(5deg) scale(1.02)';
        });
        
        dashboardPreview.addEventListener('mouseleave', function() {
            this.style.transform = 'perspective(1000px) rotateY(-15deg) rotateX(10deg) scale(1)';
        });
    }
    
    // Deployment items animation
    const deploymentItems = document.querySelectorAll('.deployment-item');
    deploymentItems.forEach((item, index) => {
        setTimeout(() => {
            item.style.opacity = '1';
            item.style.transform = 'translateX(0)';
        }, index * 200);
        
        item.style.opacity = '0';
        item.style.transform = 'translateX(-20px)';
        item.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    });
    
    // Simulate real-time updates for demo
    function simulateRealTimeUpdates() {
        const runningStatus = document.querySelector('.deployment-status.running');
        if (runningStatus) {
            setInterval(() => {
                const spinner = runningStatus.querySelector('.fa-spinner');
                if (spinner) {
                    spinner.style.transform = `rotate(${Date.now() / 10 % 360}deg)`;
                }
            }, 50);
        }
        
        // Simulate deployment completion
        setTimeout(() => {
            if (runningStatus) {
                runningStatus.classList.remove('running');
                runningStatus.classList.add('success');
                runningStatus.innerHTML = '<i class="fas fa-check-circle"></i>';
                
                const deploymentInfo = runningStatus.nextElementSibling;
                if (deploymentInfo) {
                    const timeElement = deploymentInfo.querySelector('.deployment-time');
                    if (timeElement) {
                        timeElement.textContent = 'Just completed';
                    }
                }
            }
        }, 5000);
    }
    
    // Parallax effect for hero section
    window.addEventListener('scroll', function() {
        const scrolled = window.pageYOffset;
        const heroVisual = document.querySelector('.hero-visual');
        if (heroVisual) {
            const rate = scrolled * -0.3;
            heroVisual.style.transform = `translateY(${rate}px)`;
        }
    });
    
    // Button click effects
    document.querySelectorAll('.btn').forEach(button => {
        button.addEventListener('click', function(e) {
            // Create ripple effect
            const rect = this.getBoundingClientRect();
            const ripple = document.createElement('div');
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                transform: scale(0);
                animation: ripple 0.6s ease-out;
                pointer-events: none;
            `;
            
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
    
    // Add CSS for ripple animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes ripple {
            to {
                transform: scale(2);
                opacity: 0;
            }
        }
        
        .mobile-menu-toggle {
            transition: transform 0.3s ease;
        }
        
        .mobile-menu-toggle:hover {
            transform: scale(1.1);
        }
        
        .nav-links.active {
            display: flex;
            flex-direction: column;
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            padding: 1rem;
            border-top: 1px solid var(--border-color);
            box-shadow: var(--shadow-md);
        }
        
        @media (max-width: 768px) {
            .nav-links {
                display: none;
            }
        }
    `;
    document.head.appendChild(style);
    
    // Initialize simulations
    simulateRealTimeUpdates();
    
    // Preload critical images
    const criticalImages = [
        '/static/images/favicon.ico'
    ];
    
    criticalImages.forEach(src => {
        const img = new Image();
        img.src = src;
    });
    
    // Performance monitoring
    if ('performance' in window) {
        window.addEventListener('load', function() {
            setTimeout(() => {
                const perfData = performance.getEntriesByType('navigation')[0];
                console.log('Page load time:', perfData.loadEventEnd - perfData.fetchStart, 'ms');
            }, 0);
        });
    }
    
    // Add loading states for buttons that navigate
    document.querySelectorAll('a[href="/login"], a[href="/api"]').forEach(link => {
        link.addEventListener('click', function() {
            this.style.opacity = '0.7';
            this.style.pointerEvents = 'none';
            
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
            
            // Reset after 3 seconds if page hasn't loaded
            setTimeout(() => {
                this.innerHTML = originalText;
                this.style.opacity = '1';
                this.style.pointerEvents = 'auto';
            }, 3000);
        });
    });
});

// Add some Easter eggs for developers
console.log(`
🚀 Trigger Deploy Server
═══════════════════════

Built with ❤️ for streamlined deployment management.

Features:
• Multi-server deployment
• Real-time monitoring  
• Smart notifications
• Docker integration
• Comprehensive analytics

Version: 1.0.0
`);

// Real-time System Health Monitoring for Landing Page
function updateSystemHealth() {
    fetch('/api/health/realtime')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update CPU usage
                const cpuElement = document.querySelector('.health-metric[data-metric="cpu"] .metric-value');
                const cpuBar = document.querySelector('.health-metric[data-metric="cpu"] .metric-bar-fill');
                if (cpuElement && cpuBar) {
                    cpuElement.textContent = data.system.cpu_usage + '%';
                    cpuBar.style.width = data.system.cpu_usage + '%';
                    
                    // Color coding based on usage
                    if (data.system.cpu_usage > 80) {
                        cpuBar.style.background = 'linear-gradient(45deg, #ff6b6b, #ee5a52)';
                    } else if (data.system.cpu_usage > 60) {
                        cpuBar.style.background = 'linear-gradient(45deg, #ffd93d, #ff9800)';
                    } else {
                        cpuBar.style.background = 'linear-gradient(45deg, #6bcf7f, #4caf50)';
                    }
                }
                
                // Update Memory usage
                const memoryElement = document.querySelector('.health-metric[data-metric="memory"] .metric-value');
                const memoryBar = document.querySelector('.health-metric[data-metric="memory"] .metric-bar-fill');
                if (memoryElement && memoryBar) {
                    memoryElement.textContent = data.system.memory_usage + '%';
                    memoryBar.style.width = data.system.memory_usage + '%';
                    
                    // Color coding based on usage
                    if (data.system.memory_usage > 80) {
                        memoryBar.style.background = 'linear-gradient(45deg, #ff6b6b, #ee5a52)';
                    } else if (data.system.memory_usage > 60) {
                        memoryBar.style.background = 'linear-gradient(45deg, #ffd93d, #ff9800)';
                    } else {
                        memoryBar.style.background = 'linear-gradient(45deg, #6bcf7f, #4caf50)';
                    }
                }
                
                // Update Disk usage
                const diskElement = document.querySelector('.health-metric[data-metric="disk"] .metric-value');
                const diskBar = document.querySelector('.health-metric[data-metric="disk"] .metric-bar-fill');
                if (diskElement && diskBar) {
                    diskElement.textContent = data.system.disk_usage + '%';
                    diskBar.style.width = data.system.disk_usage + '%';
                    
                    // Color coding based on usage
                    if (data.system.disk_usage > 80) {
                        diskBar.style.background = 'linear-gradient(45deg, #ff6b6b, #ee5a52)';
                    } else if (data.system.disk_usage > 60) {
                        diskBar.style.background = 'linear-gradient(45deg, #ffd93d, #ff9800)';
                    } else {
                        diskBar.style.background = 'linear-gradient(45deg, #6bcf7f, #4caf50)';
                    }
                }
                
                // Update status indicator
                const statusIndicator = document.querySelector('.system-status-indicator');
                if (statusIndicator) {
                    const avgUsage = (data.system.cpu_usage + data.system.memory_usage + data.system.disk_usage) / 3;
                    if (avgUsage > 80) {
                        statusIndicator.className = 'system-status-indicator status-critical';
                        statusIndicator.textContent = 'High Load';
                    } else if (avgUsage > 60) {
                        statusIndicator.className = 'system-status-indicator status-warning';
                        statusIndicator.textContent = 'Moderate Load';
                    } else {
                        statusIndicator.className = 'system-status-indicator status-healthy';
                        statusIndicator.textContent = 'Healthy';
                    }
                }
                
                // Update last updated timestamp
                const timestampElement = document.querySelector('.health-last-updated');
                if (timestampElement) {
                    const now = new Date();
                    timestampElement.textContent = `Last updated: ${now.toLocaleTimeString()}`;
                }
            }
        })
        .catch(error => {
            console.warn('Could not fetch system health data:', error);
            // Set fallback values if API is not available
            const statusIndicator = document.querySelector('.system-status-indicator');
            if (statusIndicator) {
                statusIndicator.className = 'system-status-indicator status-offline';
                statusIndicator.textContent = 'Monitoring Offline';
            }
        });
}

// Initialize system health monitoring
function initSystemHealth() {
    // Initial load
    updateSystemHealth();
    
    // Update every 5 seconds
    setInterval(updateSystemHealth, 5000);
}

// Start system health monitoring when page loads
if (document.querySelector('.metrics-card')) {
    initSystemHealth();
}

// Service Worker registration for PWA capabilities (if needed)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // Uncomment when you have a service worker
        // navigator.serviceWorker.register('/sw.js');
    });
}
