
function searchRoom(event) {
    let input = document.getElementById("searchbar").value.toLowerCase();
    if (input == "") {
        resetSearch();
    } else {
        filterRooms(input);
    }
}

function filterRooms(input) {
    const table = document.getElementById("room-table");
    let nodes = table.getElementsByClassName("purchase");
    for (node of nodes) {
        let rname = node.getElementsByClassName("rname")[0].innerText.toLowerCase();
        let pname = node.getElementsByClassName("pname")[0].innerText.toLowerCase();
        if (rname.includes(input) || pname.includes(input)) {
            node.style.display = "grid";
        } else {
            node.style.display = "none";
        }
    }  
}

function resetSearch() {
    const table = document.getElementById("room-table");
    document.getElementById("searchbar").value = "";
    let nodes = table.getElementsByClassName("purchase");
    for (node of nodes) { node.style.display = "grid" };
}
