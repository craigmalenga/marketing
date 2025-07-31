/**
 * Report functionality
 */

// Credit Performance Report functions
function loadCreditPerformanceFilters() {
    fetch('/api/reports/available-filters')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Populate product category filter
                const categorySelect = document.getElementById('product-category');
                categorySelect.innerHTML = '<option value="">All Categories</option>';
                
                data.filters.product_categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category;
                    option.textContent = category;
                    categorySelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error loading filters:', error);
        });
}

function loadCreditPerformanceReport() {
    // Show loading indicator
    const loadingDiv = document.getElementById('loading-indicator');
    const tbody = document.getElementById('credit-performance-tbody');
    const tfoot = document.getElementById('credit-performance-tfoot');
    
    loadingDiv.classList.remove('hidden');
    tbody.innerHTML = '';
    tfoot.innerHTML = '';
    
    // Get filter values
    const params = new URLSearchParams({
        start_date: document.getElementById('start-date').value,
        end_date: document.getElementById('end-date').value,
        product_category: document.getElementById('product-category').value
    });
    
    fetch(`/api/reports/credit-performance?${params}`)
        .then(response => response.json())
        .then(data => {
            loadingDiv.classList.add('hidden');
            
            if (data.success) {
                displayCreditPerformanceReport(data.data);
                updateCreditPerformanceMetrics(data.data);
            } else {
                showAlert('Failed to load report', 'error');
            }
        })
        .catch(error => {
            loadingDiv.classList.add('hidden');
            console.error('Error loading report:', error);
            showAlert('Error loading report', 'error');
        });
}

function displayCreditPerformanceReport(data) {
    const tbody = document.getElementById('credit-performance-tbody');
    const tfoot = document.getElementById('credit-performance-tfoot');
    
    // Display rows
    let html = '';
    data.rows.forEach(row => {
        html += `
            <tr>
                <td>${row.product}</td>
                <td class="text-right">${formatNumber(row.number)}</td>
                <td class="text-right">${formatCurrency(row.average_value_credit_applied)}</td>
                <td class="text-right">${formatCurrency(row.combined_enquiry_credit_value)}</td>
                <td class="text-right">${formatCurrency(row.credit_for_applications)}</td>
                <td class="text-right">${formatPercentage(row.pull_through_rate)}</td>
                <td class="text-right">${formatCurrency(row.credit_for_processed_applications)}</td>
                <td class="text-right">${formatPercentage(row.percent_applications_processed)}</td>
                <td class="text-right">${formatCurrency(row.credit_issued_for_approved_applications)}</td>
                <td class="text-right">${formatPercentage(row.percent_processed_applications_issued)}</td>
                <td class="text-right">${formatCurrency(row.average_credit_issued_per_enquiry)}</td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
    
    // Display totals
    if (data.totals) {
        tfoot.innerHTML = `
            <tr class="font-bold bg-gray-100">
                <td>${data.totals.product}</td>
                <td class="text-right">${formatNumber(data.totals.number)}</td>
                <td class="text-right">${formatCurrency(data.totals.average_value_credit_applied)}</td>
                <td class="text-right">${formatCurrency(data.totals.combined_enquiry_credit_value)}</td>
                <td class="text-right">${formatCurrency(data.totals.credit_for_applications)}</td>
                <td class="text-right">${formatPercentage(data.totals.pull_through_rate)}</td>
                <td class="text-right">${formatCurrency(data.totals.credit_for_processed_applications)}</td>
                <td class="text-right">${formatPercentage(data.totals.percent_applications_processed)}</td>
                <td class="text-right">${formatCurrency(data.totals.credit_issued_for_approved_applications)}</td>
                <td class="text-right">${formatPercentage(data.totals.percent_processed_applications_issued)}</td>
                <td class="text-right">${formatCurrency(data.totals.average_credit_issued_per_enquiry)}</td>
            </tr>
        `;
    }
}

function updateCreditPerformanceMetrics(data) {
    // Find top performing product by approval rate
    let topProduct = null;
    let maxApprovalRate = 0;
    
    data.rows.forEach(row => {
        if (row.percent_processed_applications_issued > maxApprovalRate) {
            maxApprovalRate = row.percent_processed_applications_issued;
            topProduct = row.product;
        }
    });
    
    document.getElementById('top-product').textContent = topProduct || '-';
    document.getElementById('avg-pull-through').textContent = formatPercentage(data.totals.pull_through_rate);
    document.getElementById('total-credit-issued').textContent = formatCurrency(data.totals.credit_issued_for_approved_applications);
}

function resetCreditFilters() {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);
    
    document.getElementById('start-date').value = startDate.toISOString().split('T')[0];
    document.getElementById('end-date').value = endDate.toISOString().split('T')[0];
    document.getElementById('product-category').value = '';
    
    loadCreditPerformanceReport();
}

function exportCreditPerformanceReport() {
    const params = {
        start_date: document.getElementById('start-date').value,
        end_date: document.getElementById('end-date').value,
        product_category: document.getElementById('product-category').value
    };
    
    fetch('/api/reports/export/credit-performance', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    })
    .then(response => {
        if (response.ok) {
            return response.blob();
        }
        throw new Error('Export failed');
    })
    .then(blob => {
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `credit_performance_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showAlert('Report exported successfully', 'success');
    })
    .catch(error => {
        console.error('Error exporting report:', error);
        showAlert('Error exporting report', 'error');
    });
}

// Marketing Campaign Report functions
function loadMarketingFilters() {
    fetch('/api/reports/available-filters')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Populate campaign filter
                const campaignSelect = document.getElementById('campaign-name');
                campaignSelect.innerHTML = '<option value="">All Campaigns</option>';
                
                data.filters.campaigns.forEach(campaign => {
                    const option = document.createElement('option');
                    option.value = campaign;
                    option.textContent = campaign;
                    campaignSelect.appendChild(option);
                });
                
                // Populate ad level filter
                const adLevelSelect = document.getElementById('ad-level');
                adLevelSelect.innerHTML = '<option value="">All Ad Levels</option>';
                
                data.filters.ad_levels.forEach(adLevel => {
                    const option = document.createElement('option');
                    option.value = adLevel;
                    option.textContent = adLevel;
                    adLevelSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error loading filters:', error);
        });
}

function loadMarketingCampaignReport() {
    // Get filter values
    const params = new URLSearchParams({
        start_date: document.getElementById('start-date').value,
        end_date: document.getElementById('end-date').value,
        campaign_name: document.getElementById('campaign-name').value,
        ad_level: document.getElementById('ad-level').value
    });
    
    fetch(`/api/reports/marketing-campaign?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayMarketingCampaignReport(data.data);
                initializeMarketingCharts(data.data);
            } else {
                showAlert('Failed to load report', 'error');
            }
        })
        .catch(error => {
            console.error('Error loading report:', error);
            showAlert('Error loading report', 'error');
        });
}

function displayMarketingCampaignReport(data) {
    // Update summary metrics
    document.getElementById('marketing-cost').textContent = formatCurrency(data.summary.marketing_cost);
    document.getElementById('cost-per-enquiry').textContent = formatCurrency(data.summary.cost_per_enquiry);
    document.getElementById('cost-per-application').textContent = formatCurrency(data.summary.cost_per_application);
    document.getElementById('cost-per-approved').textContent = formatCurrency(data.summary.cost_per_approved_loan);
    document.getElementById('approval-rate').textContent = formatPercentage(data.summary.approval_rate);
    document.getElementById('credit-issued').textContent = formatCurrency(data.summary.sum_of_credit_issued);
    document.getElementById('credit-per-pound').textContent = formatCurrency(data.summary.credit_per_pound_spent);
    document.getElementById('gm-return').textContent = formatCurrency(data.summary.gross_margin_return_per_pound_spent);
    
    // Update status breakdown table
    const tbody = document.getElementById('status-breakdown-tbody');
    let html = '';
    
    data.status_breakdown.forEach(status => {
        html += `
            <tr>
                <td class="text-sm">${status.status}</td>
                <td class="text-center">${status.is_application_received}</td>
                <td class="text-center">${status.is_application_processed}</td>
                <td class="text-center">${status.is_application_approved}</td>
                <td class="text-center">${status.is_future}</td>
                <td class="text-right">${formatNumber(status.count)}</td>
                <td class="text-right">${formatCurrency(status.value)}</td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
    
    // Update insights
    document.getElementById('total-enquiries').textContent = formatNumber(data.counts.enquiries);
    document.getElementById('total-applications').textContent = formatNumber(data.counts.applications);
    document.getElementById('total-processed').textContent = formatNumber(data.counts.processed);
    document.getElementById('total-approved').textContent = formatNumber(data.counts.approved);
    
    document.getElementById('avg-credit-approved').textContent = formatCurrency(data.summary.average_credit_issued_per_successful_app);
    document.getElementById('expected-gm').textContent = formatCurrency(data.summary.expected_gross_margin_per_pound_spent);
    
    const processingEfficiency = data.counts.applications > 0 ? data.counts.processed / data.counts.applications : 0;
    document.getElementById('processing-efficiency').textContent = formatPercentage(processingEfficiency);
    
    const conversionRate = data.counts.enquiries > 0 ? data.counts.approved / data.counts.enquiries : 0;
    document.getElementById('conversion-rate').textContent = formatPercentage(conversionRate);
}

function initializeMarketingCharts(data) {
    // Funnel Chart
    const funnelCtx = document.getElementById('funnel-chart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (window.funnelChart) {
        window.funnelChart.destroy();
    }
    
    window.funnelChart = new Chart(funnelCtx, {
        type: 'bar',
        data: {
            labels: ['Enquiries', 'Applications', 'Processed', 'Approved'],
            datasets: [{
                label: 'Count',
                data: [
                    data.counts.enquiries,
                    data.counts.applications,
                    data.counts.processed,
                    data.counts.approved
                ],
                backgroundColor: [
                    'rgba(59, 130, 246, 0.8)',
                    'rgba(34, 197, 94, 0.8)',
                    'rgba(251, 191, 36, 0.8)',
                    'rgba(168, 85, 247, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
    
    // ROI Chart
    const roiCtx = document.getElementById('roi-chart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (window.roiChart) {
        window.roiChart.destroy();
    }
    
    window.roiChart = new Chart(roiCtx, {
        type: 'doughnut',
        data: {
            labels: ['Marketing Spend', 'Credit Issued'],
            datasets: [{
                data: [
                    data.summary.marketing_cost,
                    data.summary.sum_of_credit_issued
                ],
                backgroundColor: [
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(34, 197, 94, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + formatCurrency(context.parsed);
                        }
                    }
                }
            }
        }
    });
}

function resetMarketingFilters() {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);
    
    document.getElementById('start-date').value = startDate.toISOString().split('T')[0];
    document.getElementById('end-date').value = endDate.toISOString().split('T')[0];
    document.getElementById('campaign-name').value = '';
    document.getElementById('ad-level').value = '';
    
    loadMarketingCampaignReport();
}

function exportMarketingCampaignReport() {
    const params = {
        start_date: document.getElementById('start-date').value,
        end_date: document.getElementById('end-date').value,
        campaign_name: document.getElementById('campaign-name').value,
        ad_level: document.getElementById('ad-level').value
    };
    
    fetch('/api/reports/export/marketing-campaign', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    })
    .then(response => {
        if (response.ok) {
            return response.blob();
        }
        throw new Error('Export failed');
    })
    .then(blob => {
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `marketing_campaign_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showAlert('Report exported successfully', 'success');
    })
    .catch(error => {
        console.error('Error exporting report:', error);
        showAlert('Error exporting report', 'error');
    });
}