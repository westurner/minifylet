
// searchforthis_google-bookmarklet.js

const s=window.getSelection().toString().trim();
if(s){
    window.open("https://google.com/search?q="+encodeURIComponent(s),'_blank');
} else {
    alert("Please select some text first!");
}