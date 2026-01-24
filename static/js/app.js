// Placeholder site JS
console.log('ZNPHI ImpTracker static JS loaded');
// ============================================================================
// ATTACHMENT MANAGEMENT FUNCTIONS
// ============================================================================

/**
 * Load attachments for an activity
 */
function loadAttachments(activityId) {
    const attachmentsList = document.getElementById('attachmentsList');
    if (!attachmentsList) return;
    
    attachmentsList.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"><span class="visually-hidden">Loading...</span></div> Loading documents...';
    
    fetch(`/activities/${activityId}/attachments/`, {
        method: 'GET',
        headers: {
            'Accept': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && Object.keys(data.attachments).length > 0) {
            let html = '<div class="table-responsive"><table class="table table-sm mb-0"><thead class="table-light"><tr><th>Document Type</th><th>Filename</th><th>Version</th><th>Size</th><th>Uploaded By</th><th>Date</th><th>Actions</th></tr></thead><tbody>';
            
            for (const [docType, attachments] of Object.entries(data.attachments)) {
                attachments.forEach(att => {
                    html += `
                        <tr>
                            <td class="small">${docType}</td>
                            <td class="small"><strong>${att.filename}</strong></td>
                            <td class="small"><span class="badge ${att.is_latest ? 'bg-success' : 'bg-secondary'}">v${att.version}</span></td>
                            <td class="small text-muted">${att.file_size}</td>
                            <td class="small">${att.uploaded_by}</td>
                            <td class="small text-muted">${att.uploaded_at}</td>
                            <td class="small">
                                <a href="/attachments/${att.id}/download/" class="btn btn-link btn-sm p-0" title="Download">Download</a>
                                ${canEdit ? `<button class="btn btn-link btn-sm text-danger p-0 ms-2" onclick="deleteAttachment(${att.id}, '${att.filename}')" title="Delete">Delete</button>` : ''}
                                <button class="btn btn-link btn-sm p-0 ms-2" onclick="showVersionHistory(${activityId}, '${docType.replace(/'/g, "\\'")}')">History</button>
                            </td>
                        </tr>
                    `;
                });
            }
            
            html += '</tbody></table></div>';
            attachmentsList.innerHTML = html;
        } else {
            attachmentsList.innerHTML = '<div class="text-muted text-center py-3">No documents uploaded yet</div>';
        }
    })
    .catch(error => {
        console.error('Error loading attachments:', error);
        attachmentsList.innerHTML = '<div class="alert alert-danger" role="alert">Error loading documents</div>';
    });
}

/**
 * Upload attachment
 */
function uploadAttachment(activityId) {
    const form = document.getElementById('attachmentForm');
    const documentType = document.getElementById('documentType').value;
    const fileInput = document.getElementById('fileInput');
    const description = document.getElementById('description').value;
    const progressDiv = document.getElementById('uploadProgress');
    const progressBar = document.getElementById('progressBar');
    const uploadError = document.getElementById('uploadError');
    const uploadBtn = document.querySelector('[onclick*="uploadAttachment"]');
    
    // Validate inputs
    uploadError.classList.add('d-none');
    let hasError = false;
    
    if (!documentType) {
        document.getElementById('documentTypeError').textContent = 'Document type is required';
        hasError = true;
    } else {
        document.getElementById('documentTypeError').textContent = '';
    }
    
    if (!fileInput.files[0]) {
        document.getElementById('fileError').textContent = 'File is required';
        hasError = true;
    } else {
        document.getElementById('fileError').textContent = '';
    }
    
    if (hasError) return;
    
    // Validate file
    const file = fileInput.files[0];
    const maxSize = 50 * 1024 * 1024; // 50 MB
    const allowedExtensions = ['.pdf', '.docx', '.xlsx'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedExtensions.includes(fileExtension)) {
        document.getElementById('fileError').textContent = 'Only PDF, DOCX, and XLSX files are allowed';
        return;
    }
    
    if (file.size > maxSize) {
        document.getElementById('fileError').textContent = 'File size must be less than 50 MB';
        return;
    }
    
    // Prepare form data
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);
    formData.append('description', description);
    
    // Show progress
    progressDiv.classList.remove('d-none');
    uploadBtn.disabled = true;
    
    // Upload file
    fetch(`/activities/${activityId}/attachments/upload/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reset form
            form.reset();
            progressDiv.classList.add('d-none');
            uploadBtn.disabled = false;
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('uploadAttachmentModal'));
            modal.hide();
            
            // Show success message
            showNotification('success', data.message);
            
            // Reload attachments
            loadAttachments(activityId);
        } else {
            uploadError.textContent = data.error || 'Upload failed';
            uploadError.classList.remove('d-none');
            progressDiv.classList.add('d-none');
            uploadBtn.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error uploading file:', error);
        uploadError.textContent = 'Error uploading file: ' + error;
        uploadError.classList.remove('d-none');
        progressDiv.classList.add('d-none');
        uploadBtn.disabled = false;
    });
}

/**
 * Delete attachment
 */
function deleteAttachment(attachmentId, filename) {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
        return;
    }
    
    fetch(`/attachments/${attachmentId}/delete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('success', data.message);
            // Get activity ID from URL or current page
            const activityId = window.location.pathname.split('/')[2];
            loadAttachments(activityId);
        } else {
            showNotification('danger', data.error || 'Delete failed');
        }
    })
    .catch(error => {
        console.error('Error deleting attachment:', error);
        showNotification('danger', 'Error deleting attachment');
    });
}

/**
 * Show version history for a document type
 */
function showVersionHistory(activityId, docType) {
    fetch(`/activities/${activityId}/attachments/versions/?type=${encodeURIComponent(docType)}`, {
        method: 'GET',
        headers: {
            'Accept': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            let html = `
                <div class="modal fade" id="versionHistoryModal" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Version History - ${data.document_type}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="table-responsive">
                                    <table class="table table-sm">
                                        <thead class="table-light">
                                            <tr>
                                                <th>Version</th>
                                                <th>Filename</th>
                                                <th>Size</th>
                                                <th>Uploaded By</th>
                                                <th>Date</th>
                                                <th>Status</th>
                                            </tr>
                                        </thead>
                                        <tbody>
            `;
            
            data.versions.forEach(v => {
                const latestBadge = v.is_latest ? '<span class="badge bg-success">Latest</span>' : '';
                const deletedBadge = v.is_deleted ? '<span class="badge bg-danger">Deleted</span>' : '';
                const status = v.is_deleted ? deletedBadge : latestBadge;
                
                html += `
                    <tr>
                        <td class="small"><strong>v${v.version}</strong></td>
                        <td class="small">${v.filename}</td>
                        <td class="small text-muted">${v.file_size}</td>
                        <td class="small">${v.uploaded_by}</td>
                        <td class="small text-muted">${v.uploaded_at}</td>
                        <td class="small">${status}</td>
                    </tr>
                `;
            });
            
            html += `
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Create and show modal
            const modalContainer = document.createElement('div');
            modalContainer.innerHTML = html;
            document.body.appendChild(modalContainer);
            
            const modal = new bootstrap.Modal(document.getElementById('versionHistoryModal'));
            modal.show();
            
            // Clean up after modal closes
            document.getElementById('versionHistoryModal').addEventListener('hidden.bs.modal', () => {
                modalContainer.remove();
            });
        } else {
            showNotification('danger', 'Error loading version history');
        }
    })
    .catch(error => {
        console.error('Error loading version history:', error);
        showNotification('danger', 'Error loading version history');
    });
}

/**
 * Show notification
 */
function showNotification(type, message) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert" style="position: fixed; top: 20px; right: 20px; z-index: 9999; max-width: 400px;">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    const alertContainer = document.createElement('div');
    alertContainer.innerHTML = alertHtml;
    document.body.appendChild(alertContainer);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertContainer.remove();
    }, 5000);
}

// Initialize attachments on page load if on activity detail page
document.addEventListener('DOMContentLoaded', function() {
    const activityIdMatch = window.location.pathname.match(/activities\/(\d+)\//);
    if (activityIdMatch) {
        const activityId = activityIdMatch[1];
        loadAttachments(activityId);
    }
});