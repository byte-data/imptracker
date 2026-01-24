/**
 * Main Application JavaScript
 * 
 * Purpose: Common UX enhancements and interactions
 */

(function() {
  'use strict';

  // Wait for DOM to be ready
  document.addEventListener('DOMContentLoaded', function() {
    
    // ========================================
    // AUTO-DISMISS ALERTS
    // ========================================
    const autoDismissAlerts = document.querySelectorAll('.alert.auto-dismiss');
    autoDismissAlerts.forEach(function(alert) {
      setTimeout(function() {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
      }, 5000); // Dismiss after 5 seconds
    });

    // ========================================
    // FORM VALIDATION FEEDBACK
    // ========================================
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
      form.addEventListener('submit', function(event) {
        if (!form.checkValidity()) {
          event.preventDefault();
          event.stopPropagation();
        }
        form.classList.add('was-validated');
      }, false);
    });

    // ========================================
    // CONFIRM DIALOGS
    // ========================================
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    confirmButtons.forEach(function(button) {
      button.addEventListener('click', function(event) {
        const message = button.getAttribute('data-confirm');
        if (!confirm(message)) {
          event.preventDefault();
        }
      });
    });

    // ========================================
    // TOOLTIPS INITIALIZATION
    // ========================================
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].map(function(tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // ========================================
    // POPOVERS INITIALIZATION
    // ========================================
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    [...popoverTriggerList].map(function(popoverTriggerEl) {
      return new bootstrap.Popover(popoverTriggerEl);
    });

    // ========================================
    // ACTIVE NAV LINK HIGHLIGHTING
    // ========================================
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(function(link) {
      if (link.getAttribute('href') === currentPath) {
        link.classList.add('active');
      }
    });

    // ========================================
    // SMOOTH SCROLL TO TOP
    // ========================================
    const scrollToTopBtn = document.getElementById('scrollToTop');
    if (scrollToTopBtn) {
      window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
          scrollToTopBtn.style.display = 'block';
        } else {
          scrollToTopBtn.style.display = 'none';
        }
      });

      scrollToTopBtn.addEventListener('click', function() {
        window.scrollTo({
          top: 0,
          behavior: 'smooth'
        });
      });
    }

    // ========================================
    // TABLE ROW CLICK NAVIGATION
    // ========================================
    const clickableRows = document.querySelectorAll('tr[data-href]');
    clickableRows.forEach(function(row) {
      row.style.cursor = 'pointer';
      row.addEventListener('click', function(event) {
        // Don't trigger if clicking on a button or link
        if (event.target.tagName !== 'BUTTON' && 
            event.target.tagName !== 'A' &&
            !event.target.closest('button') &&
            !event.target.closest('a')) {
          window.location.href = row.getAttribute('data-href');
        }
      });
    });

    // ========================================
    // SELECT ALL CHECKBOXES
    // ========================================
    const selectAllCheckbox = document.getElementById('selectAll');
    if (selectAllCheckbox) {
      selectAllCheckbox.addEventListener('change', function() {
        const checkboxes = document.querySelectorAll('.row-checkbox');
        checkboxes.forEach(function(checkbox) {
          checkbox.checked = selectAllCheckbox.checked;
        });
      });
    }

    // ========================================
    // FORM DIRTY STATE TRACKING
    // ========================================
    const trackedForms = document.querySelectorAll('form[data-track-changes]');
    trackedForms.forEach(function(form) {
      let formChanged = false;
      
      form.addEventListener('change', function() {
        formChanged = true;
      });

      window.addEventListener('beforeunload', function(event) {
        if (formChanged) {
          event.preventDefault();
          event.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
          return event.returnValue;
        }
      });

      form.addEventListener('submit', function() {
        formChanged = false;
      });
    });

    // ========================================
    // COPY TO CLIPBOARD
    // ========================================
    const copyButtons = document.querySelectorAll('[data-copy]');
    copyButtons.forEach(function(button) {
      button.addEventListener('click', function() {
        const textToCopy = button.getAttribute('data-copy');
        navigator.clipboard.writeText(textToCopy).then(function() {
          // Show success feedback
          const originalText = button.innerHTML;
          button.innerHTML = '<i class="bi bi-check"></i> Copied!';
          setTimeout(function() {
            button.innerHTML = originalText;
          }, 2000);
        });
      });
    });

    // ========================================
    // FILE INPUT PREVIEW
    // ========================================
    const fileInputs = document.querySelectorAll('input[type="file"][data-preview]');
    fileInputs.forEach(function(input) {
      input.addEventListener('change', function() {
        const previewId = input.getAttribute('data-preview');
        const preview = document.getElementById(previewId);
        if (preview && input.files && input.files[0]) {
          const reader = new FileReader();
          reader.onload = function(e) {
            if (input.files[0].type.startsWith('image/')) {
              preview.innerHTML = '<img src="' + e.target.result + '" class="img-fluid" alt="Preview">';
            } else {
              preview.innerHTML = '<p class="text-muted">Selected: ' + input.files[0].name + '</p>';
            }
          };
          reader.readAsDataURL(input.files[0]);
        }
      });
    });

  }); // End DOMContentLoaded

})();
