document.addEventListener('DOMContentLoaded', function() {
    // Enable tooltips everywhere
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Enable popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Fix for table responsiveness
    const tables = document.querySelectorAll('.table-responsive');
    tables.forEach(table => {
        if (table.scrollWidth > table.clientWidth) {
            table.style.overflowX = 'auto';
        }
    });

    // Dynamic pagination for quote items if there are many
    const quoteLists = document.querySelectorAll('.quote-list');
    quoteLists.forEach(list => {
        const items = list.querySelectorAll('.quote-item');
        if (items.length > 10) {
            // Show pagination buttons
            const paginationContainer = document.createElement('div');
            paginationContainer.className = 'pagination-container mt-3 d-flex justify-content-center';
            
            const ul = document.createElement('ul');
            ul.className = 'pagination pagination-sm';
            
            // Add first page
            const firstPageLi = document.createElement('li');
            firstPageLi.className = 'page-item active';
            firstPageLi.innerHTML = '<a class="page-link" href="#" data-page="1">1</a>';
            ul.appendChild(firstPageLi);
            
            // Calculate number of pages (5 items per page)
            const pageCount = Math.ceil(items.length / 5);
            
            // Add remaining pages
            for (let i = 2; i <= pageCount; i++) {
                const li = document.createElement('li');
                li.className = 'page-item';
                li.innerHTML = `<a class="page-link" href="#" data-page="${i}">${i}</a>`;
                ul.appendChild(li);
            }
            
            paginationContainer.appendChild(ul);
            list.parentNode.appendChild(paginationContainer);
            
            // Show only items for first page initially
            items.forEach((item, index) => {
                if (index >= 5) {
                    item.style.display = 'none';
                }
            });
            
            // Add click event for pagination
            const pageLinks = paginationContainer.querySelectorAll('.page-link');
            pageLinks.forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    const page = parseInt(this.dataset.page);
                    
                    // Update active class
                    pageLinks.forEach(l => {
                        l.parentNode.classList.remove('active');
                    });
                    this.parentNode.classList.add('active');
                    
                    // Show items for selected page
                    items.forEach((item, index) => {
                        if (index >= (page - 1) * 5 && index < page * 5) {
                            item.style.display = 'block';
                        } else {
                            item.style.display = 'none';
                        }
                    });
                });
            });
        }
    });

    // Search form enhancement
    const searchForms = document.querySelectorAll('form[action*="quotes"]');
    searchForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Clear empty form fields before submitting to keep URL clean
            const inputs = this.querySelectorAll('input, select');
            inputs.forEach(input => {
                if (input.value === '') {
                    input.name = '';
                }
            });
        });
    });

    // Add animation to stat cards
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach(card => {
        const display = card.querySelector('.display-4');
        if (display) {
            const finalValue = parseInt(display.textContent);
            if (!isNaN(finalValue)) {
                display.textContent = '0';
                let currentValue = 0;
                const increment = Math.ceil(finalValue / 30);
                
                const interval = setInterval(() => {
                    currentValue += increment;
                    if (currentValue >= finalValue) {
                        currentValue = finalValue;
                        clearInterval(interval);
                    }
                    display.textContent = currentValue;
                }, 30);
            }
        }
    });

    // Enhance tables with sorting
    const tables = document.querySelectorAll('.table');
    tables.forEach(table => {
        const headers = table.querySelectorAll('th');
        headers.forEach((header, index) => {
            // Skip if the column shouldn't be sortable
            if (header.dataset.noSort === 'true') return;
            
            header.style.cursor = 'pointer';
            header.title = 'Kliknij, aby sortować';
            
            // Add sort indicators
            const sortIndicator = document.createElement('span');
            sortIndicator.className = 'ms-1 sort-indicator';
            sortIndicator.innerHTML = '⇅';
            header.appendChild(sortIndicator);
            
            header.addEventListener('click', function() {
                const isAsc = this.classList.contains('sort-asc');
                
                // Reset all headers
                headers.forEach(h => {
                    h.classList.remove('sort-asc', 'sort-desc');
                    const indicator = h.querySelector('.sort-indicator');
                    if (indicator) indicator.innerHTML = '⇅';
                });
                
                // Set sort direction
                if (isAsc) {
                    this.classList.add('sort-desc');
                    sortIndicator.innerHTML = '↓';
                } else {
                    this.classList.add('sort-asc');
                    sortIndicator.innerHTML = '↑';
                }
                
                // Sort table
                const rows = Array.from(table.querySelectorAll('tbody tr'));
                rows.sort((a, b) => {
                    const aValue = a.cells[index].textContent;
                    const bValue = b.cells[index].textContent;
                    
                    if (!isNaN(aValue) && !isNaN(bValue)) {
                        return isAsc ? bValue - aValue : aValue - bValue;
                    } else {
                        return isAsc ? 
                            bValue.localeCompare(aValue, 'pl') : 
                            aValue.localeCompare(bValue, 'pl');
                    }
                });
                
                // Reorder rows
                const tbody = table.querySelector('tbody');
                rows.forEach(row => tbody.appendChild(row));
            });
        });
    });
});
