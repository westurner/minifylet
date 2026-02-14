// searchforthis_google_scholar-bookmarklet.js

const s=window.getSelection().toString().trim();
if(s) {
    window.open("https://scholar.google.com/scholar?hl=en&as_sdt=0%2C43&q="+encodeURIComponent(s) + "&btnG=",'_blank');
} else {
    alert("Please select some text first!");
}