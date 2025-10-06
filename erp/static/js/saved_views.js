document.addEventListener('DOMContentLoaded', () => {
  const saveBtn = document.getElementById('save-view');
  const select = document.getElementById('saved-views');
  if (!saveBtn || !select) return;
  const key = `saved_views_${location.pathname}`;
  function load() {
    const views = JSON.parse(localStorage.getItem(key) || '{}');
    select.innerHTML = '<option value="">Saved views</option>';
    Object.keys(views).forEach(name => {
      const opt = document.createElement('option');
      opt.value = name;
      opt.textContent = name;
      select.appendChild(opt);
    });
  }
  saveBtn.addEventListener('click', () => {
    const name = prompt('Name this view');
    if (!name) return;
    const views = JSON.parse(localStorage.getItem(key) || '{}');
    views[name] = location.search;
    localStorage.setItem(key, JSON.stringify(views));
    load();
  });
  select.addEventListener('change', e => {
    const views = JSON.parse(localStorage.getItem(key) || '{}');
    const query = views[select.value];
    if (query !== undefined) {
      location.search = query;
    }
  });
  load();
});
