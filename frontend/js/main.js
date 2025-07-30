// Configure API URL based on environment
const API_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:5000'
  : 'https://your-backend-url.onrender.com';  // Update after Render deployment

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('chatForm');
  const submitBtn = form.querySelector('button[type="submit"]');
  const statusDiv = document.getElementById('status');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fileInput = document.querySelector('#chatFile');
    
    if (!fileInput.files.length) {
      alert('Please choose a file first');
      return;
    }

    try {
      // Disable form while processing
      submitBtn.disabled = true;
      statusDiv.textContent = 'Generating your WhatsApp Wrapped...';

      const formData = new FormData();
      formData.append('chat', fileInput.files[0]);
      formData.append('lang', 'en');  // You can make this configurable

      const response = await fetch(`${API_URL}/generate`, {
        method: 'POST',
        body: formData
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

      statusDiv.textContent = 'PDF generated successfully!';
    } catch (error) {
      console.error('Error:', error);
      statusDiv.textContent = `Error: ${error.message}`;
    } finally {
      submitBtn.disabled = false;
    }
  });
});