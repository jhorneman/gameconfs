(function () {
    var URL = "{{ url_for('bookmarklet.search', _external=True) }}?u=" + encodeURIComponent(location.href) + "&t=" + encodeURIComponent(document.title);

    var searchText = "";
    try {
        searchText = ((window.getSelection && window.getSelection()) ||
            (document.getSelection && document.getSelection()) ||
            (document.selection && document.selection.createRange && document.selection.createRange().text));
    }
    // Access is denied on https sites
    catch(e) {}

    searchText = searchText.toString();
    if (searchText.length) {
        URL += "&q=" + encodeURIComponent(searchText);
    }

    location.href = URL;
})();