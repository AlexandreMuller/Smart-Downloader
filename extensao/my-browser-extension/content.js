// Content script para interceptar apenas cliques intencionais em botões de download
console.log("Download Interceptor content script loaded");

// Intercepta apenas cliques em elementos que parecem ser botões de download
document.addEventListener('click', function(event) {
    const target = event.target;
    
    // Verifica se é um link
    if (target.tagName === 'A' || target.closest('a')) {
        const link = target.tagName === 'A' ? target : target.closest('a');
        const href = link.href;
        
        if (href && isDownloadButton(link)) {
            console.log("Download button clicked:", href);
            
            // Verifica se a extensão está habilitada
            chrome.storage.local.get(['enabled'], function(result) {
                if (result.enabled !== false) {
                    // Previne o comportamento padrão
                    event.preventDefault();
                    event.stopPropagation();
                    
                    // Envia para o aplicativo local
                    sendToLocalApp(href);
                }
            });
        }
    }
    
    // Também verifica botões que não são links mas podem iniciar downloads
    else if (target.tagName === 'BUTTON' || target.closest('button')) {
        const button = target.tagName === 'BUTTON' ? target : target.closest('button');
        
        if (isDownloadButton(button)) {
            console.log("Download button clicked (non-link):", button);
            
            chrome.storage.local.get(['enabled'], function(result) {
                if (result.enabled !== false) {
                    // Para botões não-link, tentamos encontrar o URL de download
                    const downloadUrl = findDownloadUrl(button);
                    if (downloadUrl) {
                        event.preventDefault();
                        event.stopPropagation();
                        sendToLocalApp(downloadUrl);
                    }
                }
            });
        }
    }
});

function isDownloadButton(element) {
    if (!element) return false;
    
    const text = element.textContent || element.innerText || '';
    const textLower = text.toLowerCase().trim();
    
    // Check for download-related text (more specific)
    const downloadKeywords = [
        'download', 'baixar', 'descargar', 'télécharger', 'herunterladen',
        'get file', 'save file', 'export', 'exportar'
    ];
    const hasDownloadText = downloadKeywords.some(keyword => textLower.includes(keyword));
    
    // Check for download-related classes or IDs
    const className = (element.className || '').toLowerCase();
    const id = (element.id || '').toLowerCase();
    const hasDownloadClass = className.includes('download') || id.includes('download') ||
                             className.includes('btn-download') || id.includes('btn-download');
    
    // Check for download icons (common patterns)
    const hasDownloadIcon = element.querySelector('i[class*="download"]') || 
                           element.querySelector('svg[class*="download"]') ||
                           element.querySelector('.fa-download') ||
                           textLower.includes('↓') || 
                           textLower.includes('⬇️') ||
                           textLower.includes('📁') ||
                           textLower.includes('💾');
    
    // Check for data attributes that suggest download
    const hasDownloadAttr = element.hasAttribute('data-download') ||
                           element.hasAttribute('download') ||
                           (element.getAttribute('data-action') || '').includes('download');
    
    return hasDownloadText || hasDownloadClass || hasDownloadIcon || hasDownloadAttr;
}

function findDownloadUrl(button) {
    // Try to find download URL from various attributes
    const downloadAttr = button.getAttribute('data-download-url') ||
                        button.getAttribute('data-url') ||
                        button.getAttribute('data-href') ||
                        button.getAttribute('data-file-url');
    
    if (downloadAttr) return downloadAttr;
    
    // Look for nearby links
    const nearbyLink = button.querySelector('a') || 
                      button.parentElement.querySelector('a') ||
                      button.nextElementSibling?.tagName === 'A' ? button.nextElementSibling : null;
    
    if (nearbyLink && nearbyLink.href) return nearbyLink.href;
    
    // Check for onclick handlers that might contain URLs
    const onclickAttr = button.getAttribute('onclick');
    if (onclickAttr) {
        const urlMatch = onclickAttr.match(/(?:window\.open|location\.href|document\.location)\s*=?\s*['"`]([^'"`]+)['"`]/);
        if (urlMatch) return urlMatch[1];
    }
    
    return null;
}

function sendToLocalApp(url) {
    console.log("Sending URL to local app from content script:", url);
    
    fetch("http://localhost:8080", {
        method: "POST",
        headers: {
            "Content-Type": "text/plain"
        },
        body: url
    })
    .then(response => {
        if (response.ok) {
            console.log("URL sent successfully from content script");
        } else {
            throw new Error(`Server responded with status ${response.status}`);
        }
    })
    .catch(error => {
        // Fallback: notifica o background script
        chrome.runtime.sendMessage({
            action: 'downloadUrlDetected',
            url: url
        });
    });
}