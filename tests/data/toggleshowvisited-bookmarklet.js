javascript:(function() {
    /* distinct ID to track our style block */
    var styleId = 'bookmarklet-visited-links-toggle';
    var existingStyle = document.getElementById(styleId);

    if (existingStyle) {
        /* If it exists, remove it (Toggle OFF) */
        existingStyle.remove();
    } else {
        /* If not, create it (Toggle ON) */
        var style = document.createElement('style');
        style.id = styleId;
        /* Standard visited color is usually purple (#551A8B or similar). 
           We use !important to override site CSS. */
        style.textContent = 'a:visited { color: #551A8B !important; text-decoration: underline !important; }';
        document.head.appendChild(style);
    }
})();