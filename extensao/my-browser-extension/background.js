let isEnabled = true;

// Initialize storage with default value if not set
chrome.storage.local.get(['enabled'], function(result) {
    if (result.enabled === undefined) {
        chrome.storage.local.set({enabled: true});
        isEnabled = true;
    } else {
        isEnabled = result.enabled;
    }
    console.log("Extension enabled:", isEnabled);
});

chrome.storage.onChanged.addListener(function(changes) {
    if (changes.enabled) {
        isEnabled = changes.enabled.newValue;
        console.log("Extension enabled state changed to:", isEnabled);
    }
});

// Store URLs that were clicked intentionally
let intentionalDownloadUrls = new Set();

// Only intercept downloads that were triggered by intentional clicks
chrome.downloads.onCreated.addListener(function(downloadItem) {
    console.log("Download detected:", downloadItem.url);
    
    if (!isEnabled) {
        console.log("Extension disabled, allowing normal download");
        return;
    }
    
    // Only intercept if this URL was clicked intentionally
    if (intentionalDownloadUrls.has(downloadItem.url)) {
        console.log("Intercepting intentional download:", downloadItem.url);
        
        // Remove from our tracking set
        intentionalDownloadUrls.delete(downloadItem.url);
        
        // Cancel the download
        chrome.downloads.cancel(downloadItem.id, function() {
            if (chrome.runtime.lastError) {
                console.error("Error canceling download:", chrome.runtime.lastError);
            }
            
            // Remove from history
            chrome.downloads.erase({id: downloadItem.id}, function() {
                if (chrome.runtime.lastError) {
                    console.log("Note: Could not erase download from history:", chrome.runtime.lastError);
                }
            });
            
            // Send URL to local app
            sendUrlToLocalApp(downloadItem.url);
        });
    } else {
        console.log("Allowing automatic download (not clicked intentionally):", downloadItem.url);
    }
});

// Function to send URL to local Python application
function sendUrlToLocalApp(url) {
    console.log("Attempting to send URL to local app:", url);
    
    fetch("http://localhost:8080", {
        method: "POST",
        headers: {
            "Content-Type": "text/plain",
            "Access-Control-Allow-Origin": "*"
        },
        body: url
    })
    .then(response => {
        console.log("Response status:", response.status);
        if (!response.ok) {
            throw new Error(`Server responded with status ${response.status}`);
        }
        console.log("URL sent successfully to local app");
        return response.text();
    })
    .then(data => {
        console.log("Server response:", data);
    })
    .catch(error => {
        console.error("Error sending URL to local app:", error);
        
        // Fallback: try to show notification or popup
        chrome.notifications.create({
            type: 'basic',
            iconUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
            title: 'Download Intercepted',
            message: `URL: ${url}\nFailed to send to local app. Is the downloader running?`
        }, function(notificationId) {
            if (chrome.runtime.lastError) {
                console.error("Error creating notification:", chrome.runtime.lastError);
            }
        });
    });
}

// Add notification permission to manifest if needed
chrome.runtime.onInstalled.addListener(function() {
    console.log("Download Interceptor extension installed/updated");
});

// Handle messages from content script
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    if (request.action === 'downloadUrlDetected') {
        console.log("Download URL detected from content script:", request.url);
        
        // Add to intentional downloads tracking
        intentionalDownloadUrls.add(request.url);
        
        // Clean up old URLs after 30 seconds to prevent memory leaks
        setTimeout(() => {
            intentionalDownloadUrls.delete(request.url);
        }, 30000);
        
        // Also send directly to local app as fallback
        sendUrlToLocalApp(request.url);
    }
});

function isDownloadButton(element) {
    if (!element) return false;
    
    const text = element.textContent || element.innerText || '';
    const textLower = text.toLowerCase();
    
    // Check for download-related text
    const downloadKeywords = ['download', 'baixar', 'descargar', 'télécharger', 'herunterladen'];
    const hasDownloadText = downloadKeywords.some(keyword => textLower.includes(keyword));
    
    // Check for download-related classes or IDs
    const className = element.className || '';
    const id = element.id || '';
    const hasDownloadClass = (className + ' ' + id).toLowerCase().includes('download');
    
    // Check for download icons (common patterns)
    const hasDownloadIcon = element.querySelector('i[class*="download"]') || 
                           element.querySelector('svg[*="download"]') ||
                           textLower.includes('↓') || 
                           textLower.includes('⬇');
    
    return hasDownloadText || hasDownloadClass || hasDownloadIcon;
}