// Value animation with smooth counting
const valueCache = new Map();
const animatingElements = new Set();

function formatNumber(num, decimals) {
    return num.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

function animateValue(el, start, end, duration = 400) {
    if (animatingElements.has(el)) return;
    animatingElements.add(el);
    
    const startTime = performance.now();
    const prefix = el.textContent.match(/^[^0-9.,+-]+/)?.[0] || '';
    const suffix = el.textContent.match(/[^0-9.,+-]+$/)?.[0] || '';
    const decimals = Math.max(
        (start.toString().split('.')[1] || '').length,
        (end.toString().split('.')[1] || '').length
    );
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const easeOutCubic = 1 - Math.pow(1 - progress, 3);
        const current = start + (end - start) * easeOutCubic;
        
        el.textContent = prefix + formatNumber(current, decimals) + suffix;
        
        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            el.textContent = prefix + formatNumber(end, decimals) + suffix;
            animatingElements.delete(el);
        }
    }
    
    requestAnimationFrame(update);
}

function checkValueChanges() {
    document.querySelectorAll('.animated-number').forEach(el => {
        const text = el.textContent.replace(/,/g, '');
        const numStr = text.replace(/[^0-9.-]/g, '');
        const newVal = parseFloat(numStr);
        
        if (isNaN(newVal)) return;
        
        const oldVal = valueCache.get(el);
        
        if (oldVal !== undefined && Math.abs(oldVal - newVal) > 0.001) {
            el.classList.remove('value-increase', 'value-decrease');
            void el.offsetWidth;
            el.classList.add(newVal > oldVal ? 'value-increase' : 'value-decrease');
            
            animateValue(el, oldVal, newVal);
            
            setTimeout(() => {
                el.classList.remove('value-increase', 'value-decrease');
            }, 400);
        }
        
        valueCache.set(el, newVal);
    });
}

// Check every 500ms for smoother real-time sync
setInterval(checkValueChanges, 500);
