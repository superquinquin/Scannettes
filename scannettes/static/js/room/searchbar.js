//////////// SEARCHBAR

function searchProduct(elm, containerId) {
    const container = document.getElementById(containerId);
    let input = elm.value.toLowerCase();
    if (input === "") {
        resetSearch(containerId)
    } else {
        let nodes = container.getElementsByClassName("product");
        for (node of nodes) {
            let name = node.getAttribute("name").toLowerCase();
            let barcode = node.getAttribute("barcodes").toLowerCase();
            if (name.includes(input) || barcode.includes(input)) {
                node.style.display = "grid";
            } else {
                node.style.display = "none";
            }
        }
    }
}

function resetSearch(containerId) {
    const table = document.getElementById(containerId);
    table.getElementsByClassName("searchbar")[0].value = "";
    let nodes = table.getElementsByClassName("product");
    for (node of nodes) { node.style.display = "grid" };
}
