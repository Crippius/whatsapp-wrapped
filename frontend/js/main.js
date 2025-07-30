// Configure API URL based on environment
const API_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:5000'
  : 'https://whatsapp-wrapped-wldp.onrender.com';

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('chatForm');
  const submitBtn = form.querySelector('button[type="submit"]');
  const statusDiv = document.getElementById('status');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fileInput = document.querySelector('#chatFile');
    
    if (!fileInput.files.length) {
      showStatus('Please choose a file first', 'danger');
      return;
    }

    try {
      // Disable form while processing
      submitBtn.disabled = true;
      showStatus('Generating your WhatsApp Wrapped...', 'info');

      const formData = new FormData();
      formData.append('chat', fileInput.files[0]);
      formData.append('lang', 'en');

      console.log('Sending request to:', `${API_URL}/generate`);
      const response = await fetch(`${API_URL}/generate`, {
        method: 'POST',
        body: formData,
        mode: 'cors',
        credentials: 'include'
      });

      console.log('Response received:', response);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Get the blob from the response
      const blob = await response.blob();
      console.log('Blob received:', blob);

      // Create a temporary link and trigger download
      const url = window.URL.createObjectURL(blob);
      console.log('URL created:', url);
      
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = 'whatsapp_wrapped.pdf';
      
      // Add link to document and click it
      document.body.appendChild(a);
      console.log('Triggering download...');
      a.click();
      
      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      showStatus('PDF generated successfully! Check your downloads folder.', 'success');
    } catch (error) {
      console.error('Error during PDF generation:', error);
      showStatus(`Error: ${error.message}. Check console for details.`, 'danger');
    } finally {
      submitBtn.disabled = false;
    }
  });

  function showStatus(message, type) {
    console.log(`Status update: ${type} - ${message}`);
    statusDiv.textContent = message;
    statusDiv.className = `alert alert-${type} show`;
    statusDiv.style.display = 'block';
    
    if (type === 'success' || type === 'danger') {
      setTimeout(() => {
        statusDiv.style.display = 'none';
        statusDiv.className = 'alert';
      }, 5000);
    }
  }
});