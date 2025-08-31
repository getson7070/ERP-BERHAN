(function(){
  const origFetch = window.fetch;
  window.fetch = async function(input, init){
    const spinner = document.getElementById('loading-spinner');
    spinner && spinner.classList.remove('d-none');
    try {
      const res = await origFetch(input, init);
      if (!res.ok && res.status >= 500) {
        throw new Error('server');
      }
      return res;
    } catch (err) {
      const retry = document.createElement('button');
      retry.textContent = 'Retry';
      retry.className = 'btn btn-warning position-fixed top-0 end-0 m-3';
      retry.addEventListener('click', () => {
        retry.remove();
        window.fetch(input, init);
      });
      document.body.appendChild(retry);
      throw err;
    } finally {
      spinner && spinner.classList.add('d-none');
    }
  };
})();
