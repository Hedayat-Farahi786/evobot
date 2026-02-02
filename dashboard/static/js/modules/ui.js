/**
 * UI and Animation utilities
 */

/**
 * Animates a numeric value from start to end
 * @param {HTMLElement} el - The element to animate
 * @param {number} start - Starting value
 * @param {number} end - Ending value
 * @param {number} duration - Animation duration in ms
 */
export function animateValue(el, start, end, duration = 800) {
    const startTime = performance.now();
    const text = el.textContent || '';
    const prefix = text.match(/^[^0-9.,+-]+/)?.[0] || '';
    const suffix = text.match(/[^0-9.,+-]+$/)?.[0] || '';
    
    const decimals = Math.max(
        (start.toString().split('.')[1] || '').length,
        (end.toString().split('.')[1] || '').length
    );
    
    // Determine direction for color feedback
    const isIncrease = end > start;
    const colorClass = isIncrease ? 'text-success-flash' : 'text-danger-flash';
    
    // Add visual feedback
    el.classList.add(colorClass);
    el.style.transition = 'color 0.4s ease';
    el.style.color = isIncrease ? 'var(--success)' : 'var(--danger)';
    
    const format = (num) => {
        return num.toLocaleString('en-US', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    };
    
    const step = (currentTime) => {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Ease Out Expo
        const ease = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
        const current = start + (end - start) * ease;
        
        el.textContent = prefix + format(current) + suffix;
        
        if (progress < 1) {
            requestAnimationFrame(step);
        } else {
            el.textContent = prefix + format(end) + suffix;
            
            // Reset color after animation settles
            setTimeout(() => {
                el.style.color = '';
                el.classList.remove(colorClass);
            }, 400);
        }
    };
    
    requestAnimationFrame(step);
}

/**
 * Throttled scroll helper
 */
export function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}
