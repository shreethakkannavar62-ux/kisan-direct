// ==========================================================================
// KisanDirect - Interactive Client Logic
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Menu Toggle
    const toggleBtn = document.querySelector('.mobile-toggle');
    const navMenu = document.querySelector('.nav-menu');
    if (toggleBtn && navMenu) {
        toggleBtn.addEventListener('click', () => {
            navMenu.classList.toggle('active');
        });
    }

    // 2. Registration Role Toggle (Show/Hide Farm details)
    const roleSelector = document.getElementById('reg-role');
    const farmDetailsSection = document.getElementById('farmer-extra-fields');
    if (roleSelector && farmDetailsSection) {
        function checkRole() {
            if (roleSelector.value === 'farmer') {
                farmDetailsSection.style.display = 'block';
            } else {
                farmDetailsSection.style.display = 'none';
            }
        }
        roleSelector.addEventListener('change', checkRole);
        checkRole(); // run on load
    }

    // 3. Live Price Calculator in Crop Detail Page
    const calcQtyInput = document.getElementById('calc-qty-input');
    const calcTotalDisplay = document.getElementById('calc-total-display');
    const cropUnitPrice = document.getElementById('crop-unit-price');

    if (calcQtyInput && calcTotalDisplay && cropUnitPrice) {
        const unitPrice = parseFloat(cropUnitPrice.value) || 0;
        function updateCalc() {
            const qty = parseFloat(calcQtyInput.value) || 0;
            const total = qty * unitPrice;
            calcTotalDisplay.textContent = `₹${total.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            
            // Also sync to inquiry form if present
            const inqQty = document.getElementById('inq-requested-qty');
            if (inqQty && inqQty !== calcQtyInput) {
                inqQty.value = qty;
            }
        }
        calcQtyInput.addEventListener('input', updateCalc);
        updateCalc();
    }

    // 4. Farmer Dashboard Tabs
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    if (tabButtons.length > 0) {
        tabButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                tabButtons.forEach(b => b.classList.remove('active'));
                tabPanes.forEach(p => p.style.display = 'none');

                btn.classList.add('active');
                const targetId = btn.getAttribute('data-target');
                const targetPane = document.getElementById(targetId);
                if (targetPane) {
                    targetPane.style.display = 'block';
                }
            });
        });
    }

    // 5. Instant Client-Side Filter for Crop Cards (if search box has data-instant-filter)
    const instantSearch = document.getElementById('instant-crop-search');
    if (instantSearch) {
        instantSearch.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            const cards = document.querySelectorAll('.crop-card');
            let visibleCount = 0;

            cards.forEach(card => {
                const title = card.querySelector('.crop-name')?.textContent.toLowerCase() || '';
                const category = card.querySelector('.crop-category-tag')?.textContent.toLowerCase() || '';
                const location = card.querySelector('.farmer-loc')?.textContent.toLowerCase() || '';
                const farmer = card.querySelector('.farmer-name-row')?.textContent.toLowerCase() || '';

                if (title.includes(query) || category.includes(query) || location.includes(query) || farmer.includes(query)) {
                    card.style.display = 'flex';
                    visibleCount++;
                } else {
                    card.style.display = 'none';
                }
            });

            const countEl = document.getElementById('filtered-count');
            if (countEl) {
                countEl.textContent = `${visibleCount} crops found`;
            }
        });
    }
});

// Helper function to build WhatsApp link
function openWhatsApp(phone, cropName, price, farmerName) {
    const text = encodeURIComponent(`Namaste ${farmerName} ji! I saw your listing for "${cropName}" (₹${price}/kg) on KisanDirect. I would like to inquire about availability and purchase.`);
    window.open(`https://wa.me/91${phone}?text=${text}`, '_blank');
}
