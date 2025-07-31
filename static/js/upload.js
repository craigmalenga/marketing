/**
 * File upload handling - Fixed with CSV support
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize upload zones
    initializeUploadZone('applications');
    initializeUploadZone('flg');
    initializeUploadZone('adspend');
    initializeUploadZone('mapping');
    
    // Load upload history
    loadUploadHistory();
});

function initializeUploadZone(type) {
    const dropzone = document.getElementById(`${type}-dropzone`);
    const fileInput = document.getElementById(`${type}-file`);
    
    if (!dropzone || !fileInput) {
        console.error(`Upload zone elements not found for type: ${type}`);
        return;
    }
    
    // Click to upload
    dropzone.addEventListener('click', () => fileInput.click());
    
    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(type, e.target.files[0]);
        }
    });
    
    // Drag and drop
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('drag-over');
    });
    
    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('drag-over');
    });
    
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('drag-over');
        
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(type, e.dataTransfer.files[0]);
        }
    });
}

function handleFileUpload(type, file) {
    // Updated valid extensions to include CSV
    const validExtensions = {
        'applications': ['.csv', '.xlsx', '.xls'],
        'flg': ['.csv', '.xlsx', '.xls'],
        'adspend': ['.xlsx', '.xls'],
        'mapping': ['.docx', '.doc', '.xlsx', '.xls']
    };
    
    const fileExtension = file.name.toLowerCase().substr(file.name.lastIndexOf('.'));
    if (!validExtensions[type].includes(fileExtension)) {
        showAlert(`Invalid file type. Expected: ${validExtensions[type].join(', ')}`, 'error');
        return;
    }
    
    // Show progress
    const progressDiv = document.getElementById(`${type}-progress`);
    const progressBar = progressDiv.querySelector('.progress-bar-fill');
    const resultDiv = document.getElementById(`${type}-result`);
    
    if (!progressDiv || !progressBar || !resultDiv) {
        console.error(`Progress elements not found for type: ${type}`);
        return;
    }
    
    progressDiv.classList.remove('hidden');
    resultDiv.classList.add('hidden');
    progressBar.style.width = '0%';
    
    // Create form data
    const formData = new FormData();
    formData.append('file', file);
    
    // Determine endpoint
    const endpoints = {
        'applications': '/api/upload/applications',
        'flg': '/api/upload/flg-data',
        'adspend': '/api/upload/ad-spend',
        'mapping': '/api/upload/flg-meta-mapping'
    };
    
    // Upload file
    const xhr = new XMLHttpRequest();
    
    xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            progressBar.style.width = percentComplete + '%';
        }
    });
    
    xhr.addEventListener('load', () => {
        progressDiv.classList.add('hidden');
        
        try {
            const response = JSON.parse(xhr.responseText);
            
            if (response.success) {
                showUploadSuccess(type, response, resultDiv);
                updateUploadStatus(type, 'success');
                
                // Reload upload history
                setTimeout(() => {
                    loadUploadHistory();
                }, 1000);
            } else {
                showUploadError(type, response.error || 'Upload failed', resultDiv);
                updateUploadStatus(type, 'error');
                console.error('Upload error:', response);
            }
        } catch (error) {
            console.error('Parse error:', error);
            console.error('Response text:', xhr.responseText);
            showUploadError(type, 'Invalid response from server', resultDiv);
            updateUploadStatus(type, 'error');
        }
    });
    
    xhr.addEventListener('error', () => {
        progressDiv.classList.add('hidden');
        showUploadError(type, 'Upload failed - Network error', resultDiv);
        updateUploadStatus(type, 'error');
        console.error('XHR error');
    });
    
    xhr.open('POST', endpoints[type]);
    xhr.send(formData);
}

function showUploadSuccess(type, response, resultDiv) {
    let html = '<div class="alert alert-success">';
    html += '<i class="fas fa-check-circle mr-2"></i>';
    html += response.message || 'File uploaded successfully';
    
    // Add specific details based on type
    if (type === 'applications') {
        if (response.records_processed !== undefined) {
            html += `<br>Processed: ${response.records_processed} records`;
        }
        if (response.passed_count !== undefined && response.failed_count !== undefined) {
            html += `<br>Passed: ${response.passed_count}, Failed: ${response.failed_count}`;
        }
        if (response.file_type) {
            html += `<br>File type: ${response.file_type}`;
        }
        
        // Show warnings if present
        if (response.details && response.details.warnings && response.details.warnings.length > 0) {
            html += '<br><span class="text-yellow-600">Warnings:</span>';
            response.details.warnings.forEach(warning => {
                html += `<br>• ${warning}`;
            });
        }
    } else if (type === 'flg') {
        if (response.records_processed !== undefined) {
            html += `<br>Processed: ${response.records_processed} records`;
        }
        if (response.details) {
            if (response.details.applications_created) {
                html += `<br>Applications created: ${response.details.applications_created}`;
            }
            if (response.details.products_extracted) {
                html += `<br>Products extracted: ${response.details.products_extracted}`;
            }
        }
        if (response.new_products && response.new_products.length > 0) {
            html += `<br>New products found: ${response.new_products.join(', ')}`;
        }
        if (response.unmapped_sources && response.unmapped_sources.length > 0) {
            html += `<br><span class="text-yellow-600">Unmapped marketing sources: ${response.unmapped_sources.length}</span>`;
            html += '<br><small>' + response.unmapped_sources.slice(0, 5).join(', ');
            if (response.unmapped_sources.length > 5) {
                html += ` and ${response.unmapped_sources.length - 5} more`;
            }
            html += '</small>';
        }
    } else if (type === 'adspend') {
        if (response.records_processed !== undefined) {
            html += `<br>Processed: ${response.records_processed} records`;
        }
        if (response.total_spend !== undefined) {
            html += `<br>Total spend: ${formatCurrency(response.total_spend)}`;
        }
        if (response.new_campaigns && response.new_campaigns.length > 0) {
            html += `<br>New campaigns: ${response.new_campaigns.join(', ')}`;
        }
        if (response.details && response.details.sheets_processed) {
            html += `<br>Sheets processed: ${response.details.sheets_processed}`;
        }
    } else if (type === 'mapping') {
        let created = response.details ? response.details.mappings_created : response.mappings_created || 0;
        let updated = response.details ? response.details.mappings_updated : response.mappings_updated || 0;
        html += `<br>Created: ${created} mappings`;
        html += `<br>Updated: ${updated} mappings`;
    }
    
    html += '</div>';
    resultDiv.innerHTML = html;
    resultDiv.classList.remove('hidden');
}

function showUploadError(type, error, resultDiv) {
    resultDiv.innerHTML = `
        <div class="alert alert-error">
            <i class="fas fa-exclamation-circle mr-2"></i>
            ${error}
        </div>
    `;
    resultDiv.classList.remove('hidden');
}

function updateUploadStatus(type, status) {
    const statusSpan = document.getElementById(`${type}-status`);
    if (!statusSpan) return;
    
    if (status === 'success') {
        statusSpan.innerHTML = '<i class="fas fa-check-circle text-green-500"></i>';
    } else if (status === 'error') {
        statusSpan.innerHTML = '<i class="fas fa-exclamation-circle text-red-500"></i>';
    }
}

function loadUploadHistory() {
    fetch('/api/upload-history')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayUploadHistory(data.data);
            }
        })
        .catch(error => {
            console.error('Error loading upload history:', error);
        });
}

function displayUploadHistory(history) {
    const tbody = document.getElementById('upload-history-tbody');
    if (!tbody) return;
    
    if (history.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="px-6 py-4 text-center text-gray-500">
                    No upload history available
                </td>
            </tr>
        `;
        return;
    }
    
    let html = '';
    history.forEach(item => {
        const uploadDate = new Date(item.uploaded_at).toLocaleString('en-GB');
        const statusClass = item.status === 'processed' ? 'text-green-600' : 'text-gray-600';
        const statusIcon = item.status === 'processed' ? 'check-circle' : 'clock';
        
        html += `
            <tr>
                <td class="px-6 py-4 whitespace-nowrap text-sm">${item.filename}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">${item.type}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">${uploadDate}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm ${statusClass}">
                    <i class="fas fa-${statusIcon} mr-1"></i>
                    ${item.status}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">${item.records.toLocaleString()}</td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// Utility functions
function formatCurrency(value) {
    return new Intl.NumberFormat('en-GB', {
        style: 'currency',
        currency: 'GBP',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} mb-4`;
    
    const icon = type === 'success' ? 'check-circle' : 
                 type === 'error' ? 'exclamation-circle' : 
                 type === 'warning' ? 'exclamation-triangle' : 
                 'info-circle';
    
    alertDiv.innerHTML = `<i class="fas fa-${icon} mr-2"></i>${message}`;
    
    const main = document.querySelector('main');
    if (main) {
        main.insertBefore(alertDiv, main.firstChild);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
}