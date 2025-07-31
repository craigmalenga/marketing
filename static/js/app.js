/**
 * Main application JavaScript
 */

// Global utility functions
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} mb-4`;
    alertDiv.textContent = message;
    
    const main = document.querySelector('main');
    main.insertBefore(alertDiv, main.firstChild);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

function formatCurrency(value) {
    return new Intl.NumberFormat('en-GB', {
        style: 'currency',
        currency: 'GBP',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

function formatPercentage(value, decimals = 1) {
    return (value * 100).toFixed(decimals) + '%';
}

function formatNumber(value, decimals = 0) {
    return new Intl.NumberFormat('en-GB', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value);
}

// Status Mapping Modal functionality
document.addEventListener('DOMContentLoaded', function() {
    const statusMappingBtn = document.getElementById('status-mapping-btn');
    const statusMappingModal = document.getElementById('status-mapping-modal');
    const modalClose = statusMappingModal.querySelector('.modal-close');
    const addStatusBtn = document.getElementById('add-status-btn');
    const initializeDefaultsBtn = document.getElementById('initialize-defaults-btn');
    
    // Open modal
    statusMappingBtn.addEventListener('click', function() {
        statusMappingModal.classList.remove('hidden');
        loadStatusMappings();
    });
    
    // Close modal
    modalClose.addEventListener('click', function() {
        statusMappingModal.classList.add('hidden');
    });
    
    // Close modal when clicking outside
    statusMappingModal.addEventListener('click', function(e) {
        if (e.target === statusMappingModal) {
            statusMappingModal.classList.add('hidden');
        }
    });
    
    // Add new status
    addStatusBtn.addEventListener('click', function() {
        showAddStatusForm();
    });
    
    // Initialize defaults
    initializeDefaultsBtn.addEventListener('click', function() {
        if (confirm('This will initialize default status mappings. Continue?')) {
            initializeDefaultStatusMappings();
        }
    });
});

function loadStatusMappings() {
    fetch('/api/mappings/status')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayStatusMappings(data.data);
            } else {
                showAlert('Failed to load status mappings', 'error');
            }
        })
        .catch(error => {
            console.error('Error loading status mappings:', error);
            showAlert('Error loading status mappings', 'error');
        });
}

function displayStatusMappings(mappings) {
    const container = document.getElementById('status-mappings-list');
    
    if (mappings.length === 0) {
        container.innerHTML = '<p class="text-gray-500">No status mappings found. Click "Initialize Defaults" to add default mappings.</p>';
        return;
    }
    
    let html = `
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status Name</th>
                    <th class="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">App Received</th>
                    <th class="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">App Processed</th>
                    <th class="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">App Approved</th>
                    <th class="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Future</th>
                    <th class="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
    `;
    
    mappings.forEach(mapping => {
        html += `
            <tr>
                <td class="px-4 py-2 text-sm">${mapping.status_name}</td>
                <td class="px-4 py-2 text-center">
                    <input type="checkbox" ${mapping.is_application_received ? 'checked' : ''} 
                           onchange="updateStatusMapping(${mapping.id}, 'is_application_received', this.checked)">
                </td>
                <td class="px-4 py-2 text-center">
                    <input type="checkbox" ${mapping.is_application_processed ? 'checked' : ''} 
                           onchange="updateStatusMapping(${mapping.id}, 'is_application_processed', this.checked)">
                </td>
                <td class="px-4 py-2 text-center">
                    <input type="checkbox" ${mapping.is_application_approved ? 'checked' : ''} 
                           onchange="updateStatusMapping(${mapping.id}, 'is_application_approved', this.checked)">
                </td>
                <td class="px-4 py-2 text-center">
                    <input type="checkbox" ${mapping.is_future ? 'checked' : ''} 
                           onchange="updateStatusMapping(${mapping.id}, 'is_future', this.checked)">
                </td>
                <td class="px-4 py-2 text-center">
                    <button onclick="deleteStatusMapping(${mapping.id})" class="text-red-600 hover:text-red-800">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

function updateStatusMapping(id, field, value) {
    const data = {};
    data[field] = value ? 1 : 0;
    
    fetch(`/api/mappings/status/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            showAlert('Failed to update status mapping', 'error');
            loadStatusMappings(); // Reload to revert
        }
    })
    .catch(error => {
        console.error('Error updating status mapping:', error);
        showAlert('Error updating status mapping', 'error');
        loadStatusMappings(); // Reload to revert
    });
}

function deleteStatusMapping(id) {
    if (!confirm('Are you sure you want to delete this status mapping?')) {
        return;
    }
    
    fetch(`/api/mappings/status/${id}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Status mapping deleted successfully', 'success');
            loadStatusMappings();
        } else {
            showAlert('Failed to delete status mapping', 'error');
        }
    })
    .catch(error => {
        console.error('Error deleting status mapping:', error);
        showAlert('Error deleting status mapping', 'error');
    });
}

function showAddStatusForm() {
    const form = `
        <div class="bg-gray-50 p-4 rounded mb-4">
            <h4 class="font-semibold mb-2">Add New Status</h4>
            <div class="space-y-2">
                <input type="text" id="new-status-name" placeholder="Status name" class="form-input">
                <div class="flex space-x-4">
                    <label class="flex items-center">
                        <input type="checkbox" id="new-is-received" class="mr-2">
                        App Received
                    </label>
                    <label class="flex items-center">
                        <input type="checkbox" id="new-is-processed" class="mr-2">
                        App Processed
                    </label>
                    <label class="flex items-center">
                        <input type="checkbox" id="new-is-approved" class="mr-2">
                        App Approved
                    </label>
                    <label class="flex items-center">
                        <input type="checkbox" id="new-is-future" class="mr-2">
                        Future
                    </label>
                </div>
                <div class="flex space-x-2">
                    <button onclick="saveNewStatus()" class="btn-primary btn-sm">Save</button>
                    <button onclick="loadStatusMappings()" class="btn-secondary btn-sm">Cancel</button>
                </div>
            </div>
        </div>
    `;
    
    const container = document.getElementById('status-mappings-list');
    container.insertAdjacentHTML('afterbegin', form);
}

function saveNewStatus() {
    const statusName = document.getElementById('new-status-name').value;
    if (!statusName) {
        alert('Please enter a status name');
        return;
    }
    
    const data = {
        status_name: statusName,
        is_application_received: document.getElementById('new-is-received').checked ? 1 : 0,
        is_application_processed: document.getElementById('new-is-processed').checked ? 1 : 0,
        is_application_approved: document.getElementById('new-is-approved').checked ? 1 : 0,
        is_future: document.getElementById('new-is-future').checked ? 1 : 0
    };
    
    fetch('/api/mappings/status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Status mapping added successfully', 'success');
            loadStatusMappings();
        } else {
            showAlert(data.error || 'Failed to add status mapping', 'error');
        }
    })
    .catch(error => {
        console.error('Error adding status mapping:', error);
        showAlert('Error adding status mapping', 'error');
    });
}

function initializeDefaultStatusMappings() {
    fetch('/api/mappings/status/initialize', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            loadStatusMappings();
        } else {
            showAlert('Failed to initialize default mappings', 'error');
        }
    })
    .catch(error => {
        console.error('Error initializing default mappings:', error);
        showAlert('Error initializing default mappings', 'error');
    });
}

// Make functions available globally
window.showAlert = showAlert;
window.formatCurrency = formatCurrency;
window.formatPercentage = formatPercentage;
window.formatNumber = formatNumber;
window.updateStatusMapping = updateStatusMapping;
window.deleteStatusMapping = deleteStatusMapping;
window.saveNewStatus = saveNewStatus;