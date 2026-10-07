const runtime = 'https://cdn.jsdelivr.net/npm/@stlite/browser@0.85.1/build/stlite.js';
const boot = document.getElementById('boot');
const observer = new MutationObserver(() => {
  if (document.getElementById('jp-ready')) {
    boot.remove();
    observer.disconnect();
  }
});
observer.observe(document.getElementById('root'), { childList: true, subtree: true });
const longLoad = setTimeout(() => {
  const message = document.getElementById('boot-message');
  if (message) message.textContent = 'O primeiro carregamento está demorando um pouco. Mantenha esta página aberta; o painel precisa de conexão com a internet.';
}, 60000);
try {
  const { mount } = await import(runtime);
  const paths = ['app.py', 'data/municipio.geojson', 'data/indicadores.json', 'data/locais-votacao.json', 'vendor/leaflet.js', 'vendor/leaflet.css', 'vendor/leaflet.markercluster.js', 'vendor/MarkerCluster.css', 'map.html', 'theme.css', 'assets/ufpb-logo.png'];
  const files = Object.fromEntries(await Promise.all(paths.map(async path => {
    const response = await fetch(new URL(path, import.meta.url));
    if (!response.ok) throw new Error(`Não foi possível carregar ${path}.`);
    return [path, path.endsWith('.png') ? new Uint8Array(await response.arrayBuffer()) : await response.text()];
  })));
  mount({
    entrypoint: 'app.py', files,
    streamlitConfig: {
      'theme.base': 'light', 'theme.primaryColor': '#cb102a',
      'theme.backgroundColor': '#f6f7f9', 'theme.secondaryBackgroundColor': '#ffffff',
      'theme.textColor': '#17202d', 'theme.font': 'sans serif',
      'client.toolbarMode': 'viewer', 'browser.gatherUsageStats': false,
    },
  }, document.getElementById('root'));
} catch (error) {
  clearTimeout(longLoad);
  observer.disconnect();
  document.getElementById('boot-message').textContent = 'Não foi possível abrir o painel. Confira sua conexão e tente novamente.';
  document.querySelector('.progress').remove();
  const retry = document.createElement('button');
  retry.textContent = 'Tentar novamente';
  retry.addEventListener('click', () => location.reload());
  document.querySelector('.boot-card').append(retry);
  console.error(error);
}
