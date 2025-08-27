// Configure API URL based on environment
const API_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:5000'
  : 'https://whatsapp-wrapped-wldp.onrender.com';

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('chatForm');
  const submitBtn = form.querySelector('button[type="submit"]');
  const statusDiv = document.getElementById('status');
  const loadingDiv = document.getElementById('loading');
  let progressInterval = null;
  let currentRequestId = null;

  // Disable submit button by default
  submitBtn.disabled = true;

  // Check backend health on page load with timeout
  const healthCheckTimeout = setTimeout(() => {
    showStatus('The server is taking a lot of time starting up, reload the website in about a minute to generate your PDF', 'danger');
  }, 10000); // 10 second timeout

  checkBackendHealth().then(() => {
    clearTimeout(healthCheckTimeout);
  });

  async function checkBackendHealth() {
    try {
      // console.log('Checking backend health...');
      const response = await fetch(`${API_URL}/health`, {
        method: 'GET',
        mode: 'cors'
      });

      if (!response.ok) {
        throw new Error(`Backend health check failed: ${response.status}`);
      }

      const data = await response.json();
      // console.log('Backend health status:', data);

      if (data.status === 'ok') {
        submitBtn.disabled = false;
      } else {
        showStatus('Backend service is experiencing issues. Please try again later.', 'warning');
        submitBtn.disabled = true;
      }
    } catch (error) {
      console.error('Backend health check failed:', error);
      showStatus('Backend service is currently unavailable. Please try again later.', 'danger');
      submitBtn.disabled = true;
    }
  }

  async function pollProgress(requestId) {
    if (!requestId) {
      console.error('No request ID provided for progress polling');
      return;
    }

    try {
      // console.log(`Polling progress for request ${requestId}...`);
      const response = await fetch(`${API_URL}/progress/${requestId}`, {
        method: 'GET',
        mode: 'cors'
      });

      if (!response.ok) {
        if (response.status === 404) {
          console.warn('Progress data not found - request might be completed');
          clearInterval(progressInterval);
          progressInterval = null;
          return;
        }
        throw new Error(`Failed to fetch progress: ${response.status}`);
      }

      const data = await response.json();
      // console.log('Progress update:', data);

      // Update progress display
      updateProgressDisplay(data);

      // When complete, download the PDF
      if (data.status === 'completed') {
        // console.log('PDF generation complete, downloading...');
        clearInterval(progressInterval);
        progressInterval = null;
        
        // Download the PDF
        const pdfResponse = await fetch(`${API_URL}/download/${requestId}`, {
          method: 'GET',
          mode: 'cors'
        });
        
        if (!pdfResponse.ok) {
          throw new Error('Failed to download PDF');
        }
        
        const blob = await pdfResponse.blob();
        const url = window.URL.createObjectURL(blob);
       
        // Get filename from Content-Disposition header or use default
        let filename = 'whatsapp_wrapped.pdf';
        const disposition = pdfResponse.headers.get('Content-Disposition');
        if (disposition && disposition.includes('filename=')) {
          const filenameMatch = disposition.match(/filename=(.+)/);
          if (filenameMatch.length > 1) {
            filename = decodeURIComponent(filenameMatch[1].replace(/["']/g, ''));
          }
        }
        
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showStatus('PDF generated successfully! Check your downloads folder.', 'success');
      }
      
      // Stop polling if process errored
      if (data.status === 'error') {
        // console.log(`Progress polling stopped due to error: ${data.error}`);
        clearInterval(progressInterval);
        progressInterval = null;
        showStatus(`Error: ${data.error}`, 'danger');
      }
    } catch (error) {
      console.error('Error polling progress:', error);
      clearInterval(progressInterval);
      progressInterval = null;
      showStatus('Lost connection to server', 'danger');
    }
  }

  function updateProgressDisplay(data) {
    // console.log('Updating progress display:', data);
    const statusMessages = {
      'not_started': 'Preparing to generate PDF...',
      'starting': 'Starting PDF generation...',
      'generating': 'Generating PDF...',
      'finalizing': 'Finalizing PDF...',
      'completed': 'PDF generation complete!',
      'error': 'Error generating PDF'
    };

    const message = statusMessages[data.status] || 'Processing...';
    const progress = Math.round(data.progress);

    loadingDiv.innerHTML = `
      <div class="progress-container">
        <div class="progress">
          <div class="progress-bar" role="progressbar" style="width: ${progress}%" 
               aria-valuenow="${progress}" aria-valuemin="0" aria-valuemax="100">
            ${progress}%
          </div>
        </div>
        <div class="status-text mt-2">${message}</div>
      </div>
    `;
  }

  function stopProgressPolling() {
    // console.log('Stopping progress polling');
    if (progressInterval) {
      clearInterval(progressInterval);
      progressInterval = null;
    }
    currentRequestId = null;
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fileInput = document.querySelector('#chatFile');
    
    if (!fileInput.files.length) {
      showStatus('Please choose a file first', 'danger');
      return;
    }

    try {
      stopProgressPolling();
      loadingDiv.innerHTML = '';
      submitBtn.disabled = true;
      showStatus('Starting PDF generation...', 'info');

      const formData = new FormData();
      formData.append('chat', fileInput.files[0]);
      const langSelect = document.getElementById('langSelect');
      formData.append('lang', langSelect.value);

      // console.log('Sending request to:', `${API_URL}/generate`);
      const response = await fetch(`${API_URL}/generate`, {
        method: 'POST',
        body: formData,
        mode: 'cors'
      });

      // console.log('Response received:', response);
      // console.log('Response headers:', [...response.headers.entries()]);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      currentRequestId = data.request_id;
      // console.log('Received request ID:', currentRequestId);
      
      if (currentRequestId) {
        // console.log('Starting progress polling for request:', currentRequestId);
        progressInterval = setInterval(() => pollProgress(currentRequestId), 1000);
        
        updateProgressDisplay({
          status: 'starting',
          progress: 0
        });
      } else {
        console.warn('No request ID received from server');
        throw new Error('No request ID received from server');
      }
    } catch (error) {
      console.error('Error during PDF generation:', error);
      showStatus(`Error: ${error.message}. Check console for details.`, 'danger');
      stopProgressPolling();
    } finally {
      submitBtn.disabled = false;
    }
  });

  function showStatus(message, type) {
    // console.log(`Status update: ${type} - ${message}`);
    statusDiv.textContent = message;
  
    statusDiv.className = `alert alert-${type} show`;
    
    if (type === 'success' || type === 'danger') {
      setTimeout(() => {
        statusDiv.style.transform = 'translateY(200%)';
        setTimeout(() => {
          statusDiv.style.display = 'none';
          statusDiv.className = 'alert';
        }, 300);
      }, 5000);
    }
  }
});