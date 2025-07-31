/**
 * File upload handling
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
    // Validate file type
    const validExtensions = {
        'applications': ['.xlsx', '.xls'],
        'flg': ['.xlsx', '.xls'],
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
    
    progressDiv.classList.remove('hidden');
    resultDiv.classList.add('hidden');
    
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
            }
        } catch (error) {
            showUploadError(type, 'Invalid response from server', resultDiv);
            updateUploadStatus(type, 'error');
        }
    });
    
    xhr.addEventListener('error', () => {
        progressDiv.classList.add('hidden');
        showUploadError(type, 'Upload failed', resultDiv);
        updateUploadStatus(type, 'error');
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
        html += `<br>Processed: ${response.records_processed} records`;
        html += `<br>Passed: ${response.passed_count}, Failed: ${response.failed_count}`;
    } else if (type === 'flg') {
        html += `<br>Processed: ${response.records_processed} records`;
        if (response.new_products && response.new_products.length > 0) {
            html += `<br>New products found: ${response.new_products.join(', ')}`;
        }
        if (response.unmapped_sources && response.unmapped_sources.length > 0) {
            html += `<br><span class="text-yellow-600">Unmapped marketing sources: ${response.unmapped_sources.length}</span>`;
        }
    } else if (type === 'adspend') {
        html += `<br>Processed: ${response.records_processed} records`;
        html += `<br>Total spend: ${formatCurrency(response.total_spend)}`;
        if (response.new_campaigns && response.new_campaigns.length > 0) {
            html += `<br>New campaigns: ${response.new_campaigns.join(', ')}`;
        }
    } else if (type === 'mapping') {
        html += `<br>Created: ${response.mappings_created} mappings`;
        html += `<br>Updated: ${response.mappings_updated} mappings`;
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