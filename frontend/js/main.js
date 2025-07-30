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
      formData.append('lang', 'en');  // You can make this configurable

      const response = await fetch(`${API_URL}/generate`, {
        method: 'POST',
        body: formData,
        mode: 'cors',
        credentials: 'include',
        headers: {
          'Accept': 'application/pdf'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'whatsapp_wrapped.pdf';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      showStatus('PDF generated successfully!', 'success');
    } catch (error) {
      console.error('Error:', error);
      showStatus(`Error: ${error.message}`, 'danger');
    } finally {
      submitBtn.disabled = false;
    }
  });

  function showStatus(message, type) {
    statusDiv.textContent = message;
    statusDiv.className = `alert alert-${type}`;
    statusDiv.style.display = 'block';
    
    if (type === 'success' || type === 'danger') {
      setTimeout(() => {
        statusDiv.style.display = 'none';
      }, 5000);
    }
  }
});