document.addEventListener('DOMContentLoaded', function() {
    const toggle = document.getElementById('toggleDownloader');

    // Carrega estado atual
    chrome.storage.local.get(['enabled'], function(result) {
        toggle.checked = result.enabled !== undefined ? result.enabled : true;
    });

    // Atualiza estado quando alterado
    toggle.addEventListener('change', function() {
        chrome.storage.local.set({
            enabled: toggle.checked
        });
        console.log("Extension enabled:", toggle.checked);
    });
});